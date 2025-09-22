from typing import Optional
from sqlmodel import SQLModel, Field

class MatchBase(SQLModel):
    date: str
    time: str
    location: str
    max_players:int
    joined_players: int = 0

class Match(MatchBase, table=True):
    id: Optional[int] = Field(default= None, primary_key=True)

class MatchCreate(MatchBase):
    pass
class MatchRead(MatchBase):
    id: int
