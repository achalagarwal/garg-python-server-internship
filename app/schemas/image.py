import uuid
from datetime import datetime
from re import I
from typing import Optional, Union

from fastapi_users import models
from pydantic import UUID4, BaseModel, EmailStr, Extra, Field


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
