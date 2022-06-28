from datetime import datetime
from re import I
from typing import Optional, Union

from pydantic import UUID4, BaseModel, Extra
from typing_extensions import Literal


class LocalDataTimestamps(BaseModel):
    invoice: Union[datetime, Literal[None]]
    sku: Union[datetime, Literal[None]]


class DatabaseHasUpdates(BaseModel):
    invoice: bool
    sku: bool
