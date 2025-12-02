from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProductionStatus(str, Enum):
    PENDING = "pending"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"


class Timeline(BaseModel):
    fabric: Optional[str] = None
    cutting: Optional[str] = None
    sewing: Optional[str] = None
    shipping: Optional[str] = None

class ProductionOrder(BaseModel):
    # Identifiers
    order_id: str
    style_code: Optional[str] = None

    # Product details
    fabric: Optional[str] = None
    color: Optional[str] = None
    quantity: int = 0

    # Status
    status: ProductionStatus = ProductionStatus.PENDING

    # Timeline
    timeline: Timeline = Field(default_factory=Timeline)

    # Metadata
    brand: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Store original data if needed
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "PO-001",
                "style_code": "STYLE-ABC",
                "fabric": "100% Cotton",
                "color": "Navy Blue",
                "quantity": 1000,
                "status": "in_production",
                "timeline": {
                    "fabric": "Jan 15, 2024",
                    "cutting": "Jan 20, 2024",
                    "sewing": "Jan 25, 2024",
                    "shipping": "Feb 1, 2024"
                },
                "brand": "Nike"
            }
        }