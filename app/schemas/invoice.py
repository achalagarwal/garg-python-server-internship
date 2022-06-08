from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import UUID4, EmailStr, Field, BaseModel, Extra
from app.schemas.warehouse_inventory import WarehouseInventoryPick
from app.schemas.sku import SKU
from datetime import date

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


class WarehouseInvoice(BaseModel):
    company: str
    status: Status
    invoice_id: str
    deliver_to: Optional[str]
    warehouse_items: List[WarehouseInventoryPick]
    created_at: date
    id: UUID4

class Invoice(InvoiceCreate):
    id: UUID4
    status: Status # Enum: pending, picking, transit, complete
    class Config:  
        use_enum_values = True
        orm_mode = True
        extra = Extra.ignore

