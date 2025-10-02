from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from datetime import date, time

class MatchBase(SQLModel):
    date: date
    time: time
    location: str
    max_players:int
    joined_players: int = 0
    

class Match(MatchBase, table=True):
    id: Optional[int] = Field(default= None, primary_key=True)
    organizer_user_id: str
    organizer_first_name: str
    organizer_last_name: str

class MatchCreate(MatchBase):
    pass
class MatchRead(MatchBase):
    id: int
    # Include organizer info so the frontend can render it
    organizer_user_id: str
    organizer_first_name: str
    organizer_last_name: str

class MatchParticipant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="match.id")
    user_id: str
    first_name: str
    last_name: str
    __table_args__ = (UniqueConstraint("match_id", "user_id", name="uix_match_user"),)
