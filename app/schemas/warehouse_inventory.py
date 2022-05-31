from pydantic import UUID4, EmailStr, Field, BaseModel

class WarehouseInventoryCreate(BaseModel):
    row: int
    column: int
    sku_variant_id: UUID4
    warehouse_id: UUID4
    quantity: int

class WarehouseInventory(WarehouseInventoryCreate):
    id: UUID4
