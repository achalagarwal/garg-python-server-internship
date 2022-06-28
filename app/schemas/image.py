from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, Extra


class ImageCreate(BaseModel):
    title: Optional[str]
    timestamp: str
    data: bytes


class Image(BaseModel):
    id: UUID4
    user_id: Optional[UUID4]
    title: str
    timestamp: datetime
    base64: Optional[str]

    class Config:
        extra: Extra.ignore
