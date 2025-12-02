import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tasks import parse_excel_file
from db_client import mongo_client
from celery_app import celery_app


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db
    try:
        db = mongo_client.get_async_db()
        # Test connection
        await mongo_client.get_async_client().server_info()
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

    yield

    # Shutdown
    mongo_client.close_connections()
    logger.info("Disconnected from MongoDB")


# Create FastAPI app
app = FastAPI(
    title="Production Planning Parser API",
    description="API for parsing and managing production planning data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Production Planning Parser API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        await mongo_client.get_async_client().server_info()
        mongo_status = "connected"
    except:
        mongo_status = "error"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mongodb": mongo_status
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and parse production planning sheet asynchronously
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{file_id}{file_extension}"
    temp_file_path = f"data/_tmp/{temp_filename}"

    try:
        # Save file to temporary location
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Submit parsing task to Celery
        task = parse_excel_file.delay(temp_file_path, file.filename)

        logger.info(f"Task Created : {task}")

        return JSONResponse(
            status_code=202,
            content={
                "message": "File received successfully",
                "filename": file.filename,
                "size": file.size,
                "task_id": task.id,
                "status": "processing"
            }
        )

    except Exception as e:
        # Clean up file if something goes wrong

        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a parsing task
    """

    task_result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }


@app.get("/api/production-items")
async def get_production_items(
        skip: int = 0,
        limit: int = 100,
        style: Optional[str] = None,
        status: Optional[str] = None
):
    """
    Get production line items with optional filtering
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")

    # Build query filter
    query_filter = {}
    if style:
        query_filter["style_code"] = {"$regex": style, "$options": "i"}
    if status:
        query_filter["status"] = status

    try:
        # Get total count
        total = await db.production_orders.count_documents(query_filter)

        # Get items with pagination
        cursor = db.production_orders.find(query_filter).skip(skip).limit(limit)
        items = []

        async for doc in cursor:
            item = {
                "id": str(doc.get("_id")),
                "order_number": doc.get("order_id"),
                "style": doc.get("style_code"),
                "fabric": doc.get("fabric"),
                "color": doc.get("color"),
                "quantity": doc.get("quantity", 0),
                "status": doc.get("status", "pending"),
                "dates": doc.get("timeline", {}),
                "brand": doc.get("brand"),
                "source_file": doc.get("source_file"),
                "created_at": doc.get("created_at")
            }
            items.append(item)

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@app.get("/api/production-items/{item_id}")
async def get_production_item(item_id: str):
    """
    Get a specific production item by ID
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Convert string ID to ObjectId if it's a valid ObjectId format
        from bson import ObjectId, errors
        try:
            query = {"_id": ObjectId(item_id)}
        except errors.InvalidId:
            # If not a valid ObjectId, search by order_id field
            query = {"order_id": item_id}
        
        item = await db.production_orders.find_one(query)
        if not item:
            raise HTTPException(status_code=404, detail="Production item not found")
        
        # Convert ObjectId to string for JSON serialization
        item["id"] = str(item.pop("_id"))
        
        # Format response to match frontend expectations
        return {
            "id": item["id"],
            "order_number": item.get("order_id", ""),
            "style": item.get("style_code", ""),
            "fabric": item.get("fabric", ""),
            "color": item.get("color", ""),
            "quantity": item.get("quantity", 0),
            "status": item.get("status", "pending"),
            "dates": {
                "fabric": item.get("timeline", {}).get("fabric"),
                "cutting": item.get("timeline", {}).get("cutting"),
                "sewing": item.get("timeline", {}).get("sewing"),
                "shipping": item.get("timeline", {}).get("shipping")
            },
            "brand": item.get("brand", ""),
            "source_file": item.get("source_file", ""),
            "created_at": item.get("created_at", datetime.utcnow()).isoformat() if item.get("created_at") else None,
            "updated_at": item.get("updated_at", datetime.utcnow()).isoformat() if item.get("updated_at") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching production item {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/production-items/{item_id}")
async def delete_production_item(item_id: str):
    """
    Delete a production item
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Convert string ID to ObjectId if it's a valid ObjectId format
        from bson import ObjectId, errors
        try:
            query = {"_id": ObjectId(item_id)}
        except errors.InvalidId:
            # If not a valid ObjectId, search by order_id field
            query = {"order_id": item_id}
        
        # Check if item exists first
        item = await db.production_orders.find_one(query)
        if not item:
            raise HTTPException(status_code=404, detail="Production item not found")
        
        # Delete the item
        result = await db.production_orders.delete_one(query)
        
        if result.deleted_count == 1:
            logger.info(f"Deleted production item {item_id}")
            return {
                "message": f"Item {item_id} deleted successfully",
                "id": item_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete item")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting production item {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
