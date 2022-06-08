from typing import Optional, Union
from pydantic import UUID4, EmailStr, Field, BaseModel

class WarehouseInventoryCreate(BaseModel):
    row: int
    column: int
    sku_variant_id: Union[UUID4, None]
    # ideally this should be Union[UUID4, None] just like sku_variant_id
    # but that will break the mobile app
    sku_id: Optional[UUID4]
    warehouse_id: UUID4
    quantity: int # actual quantity in the warehouse

class WarehouseInventory(WarehouseInventoryCreate):
    id: UUID4

class WarehouseInventoryPick(BaseModel):
    row: Union[int,str]
    column: Union[int, str]
    sku_variant_id: Union[UUID4, None]
    sku_id: UUID4
    quantity: int