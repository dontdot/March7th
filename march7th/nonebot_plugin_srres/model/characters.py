from typing import Dict, List

from pydantic import BaseModel

from .common import Property, Quantity, Promotion


class CharacterType(BaseModel):
    path: str
    hash: str
    update: str

CharacterIndex = Dict[str, CharacterType]
