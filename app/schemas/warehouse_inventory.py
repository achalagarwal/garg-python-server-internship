from typing import Optional, Union
from typing_extensions import Literal
from pydantic import UUID4, EmailStr, Field, BaseModel

from app.schemas import sku_variant

class WarehouseInventoryCreate(BaseModel):
    row: int
    column: int
    sku_variant_id: Union[UUID4, Literal[None]]
    new_sku_variant: Optional[bool]
    # ideally this should be Union[UUID4, None] just like sku_variant_id
    # but that will break the mobile app
    sku_id: Optional[UUID4]
    warehouse_id: UUID4
    quantity: int # actual quantity in the warehouse

class WarehouseInventoryMove(BaseModel):

    source_row: int
    source_column: int

    target_row: int
    target_column: int

    quantity: int
    warehouse_id: UUID4
    sku_variant_id: Optional[UUID4]


class WarehouseInventory(WarehouseInventoryCreate):
    id: UUID4

class WarehouseInventoryPick(BaseModel):
    row: Union[int,str]
    column: Union[int, str]
    sku_variant_id: Union[UUID4, Literal[None]]
    sku_id: UUID4
    quantity: int