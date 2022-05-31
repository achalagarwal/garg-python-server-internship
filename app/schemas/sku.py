from re import I
import uuid
from typing import Optional
from app.schemas.image import Image, ImageCreate

from fastapi_users import models
from pydantic import UUID4, EmailStr, Field, BaseModel, Extra

class SKUCreate(BaseModel):    
    title: str
    description: Optional[str]
    price: Optional[str]
    price_unit: Optional[str]
    quantity_unit: str # uom (Unit of Measurement)
    company: str
    barcode: Optional[str]
    image: Optional[ImageCreate]
    image_id: Optional[int]
    weight: Optional[str]
    weight_unit: Optional[str]
    class Config: 
        orm_mode = True
class SKU(SKUCreate):
    id: UUID4
    class Config:
        extra: Extra.ignore

class SKUInvoice(BaseModel):
    title: str
    description: Optional[str]
    quantity_unit: str
    image_id: Optional[int]
    id: UUID4
    class Config: 
        orm_mode = True
