from enum import Enum
from typing import Any, List, Optional, Union

from fastapi_users import models
from pydantic import UUID4, EmailStr, Field, BaseModel, Extra

from app.schemas.sku import SKU

class Status(str, Enum):
    PENDING = 'PENDING'
    PICKING = 'PICKING'
    IN_TRANSIT = 'IN_TRANSIT'
    DELIVERED = 'DELIVERED'

class InvoiceCreate(BaseModel):   
    # to be updated when we have the company model
    company: str
    items: Union[List[UUID4], List[SKU]]
    quantities: List[int]
    deliver_to: Optional[str]
    invoice_id: str

class Invoice(InvoiceCreate):
    id: UUID4
    status: Status # Enum: pending, picking, transit, complete
    class Config:  
        use_enum_values = True
        orm_mode = True
        extra = Extra.ignore