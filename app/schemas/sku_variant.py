from datetime import date, datetime
from typing import Optional

from pydantic import UUID4, BaseModel, EmailStr, Field


class SKUVariantCreate(BaseModel):
    parent_sku_id: UUID4
    manufactured_date: Optional[date]
    created_at: datetime 
    image_id: Optional[UUID4]

class SKUVariant(SKUVariantCreate):
    id: UUID4
    