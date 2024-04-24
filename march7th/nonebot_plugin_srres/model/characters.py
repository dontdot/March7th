from typing import Dict, List

from pydantic import BaseModel


class CharacterType(BaseModel):
    path: str
    hash: str
    update: str

CharacterIndex = Dict[str, CharacterType]
