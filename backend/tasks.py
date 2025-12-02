import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from langchain_openai import ChatOpenAI
from celery_app import celery_app
from models import ProductionOrder
from db_client import mongo_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task
def parse_excel_file(file_path: str, original_filename: str) -> Dict[str, Any]:
    try:
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Convert DataFrame to CSV string for LLM processing
        csv_data = df.to_csv(index=False)
        
        # Initialize LangChain OpenAI client
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create prompt for parsing production data
        prompt = f"""You are an expert at parsing production planning data. 
        Given the following CSV data from an Excel sheet, extract production order information.
        
        CSV Data:
        {csv_data}
        
        Please analyze this data and return ONLY a JSON array of production orders with this exact structure:
        {{
          "orders": [
            {{
              "order_id": "string",
              "style_code": "string or null",
              "fabric": "string or null", 
              "color": "string or null",
              "quantity": number,
              "status": "pending",
              "timeline": {{
                "fabric": "YYYY-MM-DD or null",
                "cutting": "YYYY-MM-DD or null", 
                "sewing": "YYYY-MM-DD or null",
                "shipping": "YYYY-MM-DD or null"
              }},
              "brand": "string or null",
              "source_file": "{original_filename}",
              "raw_data": {{}}
            }}
          ]
        }}
        
        Rules:
        - Extract all production orders/line items from the data
        - Convert any dates to YYYY-MM-DD format
        - Use "pending" as default status
        - Extract quantities as numbers
        - Map columns intelligently (e.g., "PO", "Order", "SO" could be order_id)
        - For timeline dates, look for columns containing "fabric", "cut", "sew", "ship", "delivery" etc.
        - Return valid JSON only, no explanations"""
        
        # Get LLM response using LangChain
        response = llm.invoke(prompt)
        response_content = response.content
        logger.info(f"Response for {original_filename} IS : {response_content}")
        
        # Clean and parse JSON response
        try:
            # Extract JSON from markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                response_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.rfind("```")
                response_content = response_content[json_start:json_end].strip()
            
            parsed_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for {original_filename}: {e}")
            logger.error(f"Raw response: {response_content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        orders_data = parsed_data.get("orders", [])
        
        # Store in MongoDB using singleton client
        stored_count = 0
        if orders_data:
            # Get synchronous database connection
            db = mongo_client.get_sync_db()
            collection = db.production_orders
            
            # Insert orders
            for order_data in orders_data:
                # Add metadata
                order_data["created_at"] = datetime.utcnow()
                order_data["task_id"] = parse_excel_file.request.id
                
                # Insert into MongoDB
                collection.insert_one(order_data)
                stored_count += 1
        
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "success",
            "filename": original_filename,
            "orders_processed": len(orders_data),
            "orders_stored": stored_count,
            "task_id": parse_excel_file.request.id
        }
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            "status": "error", 
            "filename": original_filename,
            "error": str(e),
            "task_id": parse_excel_file.request.id
        }