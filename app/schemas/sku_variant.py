from pydantic import UUID4, EmailStr, Field, BaseModel
from datetime import date, datetime

class SKUVariantCreate(BaseModel):
    parent_sku_id: UUID4
    manufactured_date: date
    

class SKUVariant(SKUVariantCreate):
    id: UUID4
    created_at: datetime