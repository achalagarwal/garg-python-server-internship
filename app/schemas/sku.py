from datetime import datetime
from typing import Dict, List, Optional

from pydantic import UUID4, BaseModel, Extra

from app.schemas.image import ImageCreate


class SKUProjectedRequest(BaseModel):
    sku_id: str


class SKUCreate(BaseModel):
    title: str
    description: Optional[str]
    price: Optional[str]
    price_unit: Optional[str]
    quantity_unit: str  # uom (Unit of Measurement)
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
    id: UUID4

    class Config:
        orm_mode = True


class SKUInvoiceWithQuantity(BaseModel):
    title: str
    quantity_unit: str
    description: Optional[str]
    id: UUID4
    quantity: int


class SKUMerge(BaseModel):
    sku_ids: List[UUID4]
    primary_sku_id: Optional[UUID4]
