from uuid import UUID
from pydantic import UUID4, EmailStr, Field, BaseModel
from datetime import date, datetime

class WarehouseInventoryCreate(BaseModel):
    row: int
    column: int
    sku_variant_id: UUID4
    warehouse_id: UUID
    quantity: int

class WarehouseInventory(WarehouseInventoryCreate):
    id: UUID4
