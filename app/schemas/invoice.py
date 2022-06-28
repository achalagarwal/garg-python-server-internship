from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import UUID4, BaseModel, EmailStr, Extra, Field

from app.schemas.sku import SKU
from app.schemas.warehouse_inventory import WarehouseInventoryPick


class Status(str, Enum):
    PENDING = "PENDING"
    PICKING = "PICKING"
    READY_FOR_TRANSIT = "READY_FOR_TRANSIT"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


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


class WarehouseInvoicePatch(BaseModel):
    status: Status


class WarehouseInvoiceResponse(BaseModel):
    invoices: List[WarehouseInvoice]
    last_updated_at: datetime


class Invoice(InvoiceCreate):
    id: UUID4
    status: Status  # Enum: pending, picking, transit, complete

    class Config:
        use_enum_values = True
        orm_mode = True
        extra = Extra.ignore


# Move to warehouse_inventory
class _InventoryUpdate(BaseModel):
    sku_variant_id: UUID4
    row: int
    column: int
    quantity: int


class WarehouseInvoiceDetails(BaseModel):
    warehouse_invoice_id: UUID4
    inventory_updates: List[_InventoryUpdate]
    time_per_item: List[float]
