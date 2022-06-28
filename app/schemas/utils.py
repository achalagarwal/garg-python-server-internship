from datetime import datetime
from typing import Union

from pydantic import BaseModel
from typing_extensions import Literal


class LocalDataTimestamps(BaseModel):
    invoice: Union[datetime, Literal[None]]
    sku: Union[datetime, Literal[None]]


class DatabaseHasUpdates(BaseModel):
    invoice: bool
    sku: bool
