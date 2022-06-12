from re import I
from typing import Optional, Union
from typing_extensions import Literal

from pydantic import UUID4, BaseModel, Extra
from datetime import datetime

class LocalDataTimestamps(BaseModel):
    invoice: Union[datetime, Literal[None]]
    sku: Union[datetime, Literal[None]]

class DatabaseHasUpdates(BaseModel):
    invoice: bool
    sku: bool

