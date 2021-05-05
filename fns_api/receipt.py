from dataclasses import dataclass, field
from typing import List

from dataclasses_json import dataclass_json, config


@dataclass
class Item(object):
    name: str
    __raw_price: int = field(metadata=config(field_name="price"))
    quantity: int
    __raw_sum: int = field(metadata=config(field_name="sum"))

    @property
    def price(self) -> float:
        return self.__raw_price / 100

    @property
    def sum(self) -> float:
        return self.__raw_sum / 100


@dataclass_json
@dataclass
class Receipt(object):
    dateTime: str
    items: List[Item]
