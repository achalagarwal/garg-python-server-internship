from re import I
import uuid
from typing import Optional, Union

from fastapi_users import models
from pydantic import UUID4, EmailStr, Field, BaseModel, Extra
from datetime import datetime

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
