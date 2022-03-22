from re import I
import uuid
from typing import Optional

from fastapi_users import models
from pydantic import UUID4, EmailStr, Field, BaseModel

class ImageCreate(BaseModel):    
    title: Optional[str]
    timestamp: str 
    data: bytes

class Image(ImageCreate):
    id: UUID4
    user_id: UUID4
    title: str
    base64: str
