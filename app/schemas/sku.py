from datetime import datetime
from re import I
import uuid
from typing import Dict, List, Optional, Union
from app.schemas.image import Image, ImageCreate

from fastapi_users import models
from pydantic import UUID4, UUID1, EmailStr, Field, BaseModel, Extra


class SKUProjectedRequest(BaseModel):
    sku_id: str

class SKUCreate(BaseModel):    
    title: str
    description: Optional[str]
    price: Optional[str]
    price_unit: Optional[str]
    quantity_unit: str # uom (Unit of Measurement)
    company: str
    barcode: Optional[str]
    image: Optional[ImageCreate]
    image_id: Optional[UUID4]
    weight: Optional[str]
    weight_unit: Optional[str]
    class Config: 
        orm_mode = True
class SKU(SKUCreate):
    id: UUID4
    class Config:
        extra: Extra.ignore

class SKUGetResponse(BaseModel):
    last_updated_at: datetime
    skus: Dict

class SKUPatch(BaseModel):
    image_id: Optional[UUID4]
    price: Optional[str]
    barcode: Optional[str]
    weight: Optional[str]
class SKUInvoice(BaseModel):
    title: str
    description: Optional[str]
    quantity_unit: str
    image_id: Optional[int]
    id: UUID4
    class Config: 
        orm_mode = True
