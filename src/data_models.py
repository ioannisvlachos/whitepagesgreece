from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Phone:
    number: str
    provider: str
    type: str

@dataclass
class Name:
    first_name: str
    middle_name: Optional[str]
    last_name: str
    str_name: str

@dataclass
class Address:
    street1: str
    number1: str
    street2: Optional[str]
    number2: Optional[str]
    municipality: Optional[str]
    subregion: Optional[str]
    region: Optional[str]
    str_add: str

@dataclass
class Subscriber:
    name: Name
    phones: List[Phone]
    address: Address
    coords: dict

@dataclass
class ItemforMap:
    name: list
    phone: list
    address: list
    latitude: float
    longitude: float

@dataclass
class ItemforQuery:
    name: Optional[str]
    phone: Optional[str] 
    address: Optional[str]   
