from typing import List, TypeVar

from sqlalchemy.ext.mutable import Mutable

T = TypeVar("T")

def index_with_default(list_data: List[T], item: T, default=None):
    try:
        index = list_data.index(item)
        return index
    except ValueError:
        return default



class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value