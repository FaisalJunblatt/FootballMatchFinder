from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Match, MatchCreate, MatchRead

# correct: lowercase "prefix"
router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("", response_model=MatchRead, status_code=201)
def create_match(payload: MatchCreate, session: Session = Depends(get_session)):
    m = Match(**payload.model_dump())
    session.add(m)
    session.commit()
    session.refresh(m)
    return m

@router.get("", response_model=list[MatchRead])
def list_matches(session: Session = Depends(get_session)):
    return session.exec(select(Match).order_by(Match.date, Match.time)).all()
