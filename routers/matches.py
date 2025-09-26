from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Match, MatchCreate, MatchRead


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

@router.put("/{match_id}/join", response_model=MatchRead)   
def join_math(match_id: int, session: Session = Depends(get_session)):
    match=session.get(Match,match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.joined_players >= match.max_players:
        raise HTTPException(status_code=400, detail="Match is full")
    match.joined_players += 1
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


@router.delete("/{match_id}", status_code=204) 
def delete_match(mathc_id:int, session: Session = Depends(get_session)):
    match=session.get(Match,mathc_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    session.delete(match)
    session.commit()
    