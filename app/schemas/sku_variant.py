from pydantic import UUID4, EmailStr, Field, BaseModel
from datetime import date, datetime
from typing import Optional
class SKUVariantCreate(BaseModel):
    parent_sku_id: UUID4
    manufactured_date: Optional[date]
    created_at: datetime 

class SKUVariant(SKUVariantCreate):
    id: UUID4
    