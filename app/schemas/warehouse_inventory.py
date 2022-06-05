from pydantic import UUID4, EmailStr, Field, BaseModel

class WarehouseInventoryCreate(BaseModel):
    row: int
    column: int
    sku_variant_id: UUID4
    warehouse_id: UUID4
    quantity: int # actual quantity in the warehouse
    projected_quantity: int # final quantity in the warehouse, taking in to account the pending invoices (order + purchase)

class WarehouseInventory(WarehouseInventoryCreate):
    id: UUID4
