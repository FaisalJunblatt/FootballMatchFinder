from fastapi import APIRouter, Depends, HTTPException,Request
from sqlmodel import Session, select
from db import get_session
from models import Match, MatchCreate, MatchRead, MatchParticipant



def require_identity(request: Request):
    user_id = request.headers.get("X-User-Id")
    
    first_name = request.headers.get("X-First-Name") or request.headers.get("X-User-First-Name")
    last_name = request.headers.get("X-Last-Name") or request.headers.get("X-User-Last-Name")
    if not user_id or not first_name or not last_name:
        raise HTTPException(status_code=401, detail="Missing user identity headers")
    return user_id, first_name, last_name



router = APIRouter(prefix="/matches", tags=["matches"]) 

@router.post("", response_model=MatchRead, status_code=201)
def create_match(payload: MatchCreate, request: Request, session: Session = Depends(get_session)):
    user_id, first_name, last_name = require_identity(request)
    m=Match(**payload.model_dump(), organizer_user_id=user_id, organizer_first_name=first_name, organizer_last_name=last_name)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m

@router.get("", response_model=list[MatchRead])
def list_matches(session: Session = Depends(get_session)):
    return session.exec(select(Match).order_by(Match.date, Match.time)).all()

@router.put("/{match_id}/join", response_model=MatchRead)   
def join_match(match_id: int, request: Request,session: Session = Depends(get_session)):
    user_id, first_name, last_name = require_identity(request)
    match=session.get(Match,match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.joined_players >= match.max_players:
        raise HTTPException(status_code=400, detail="Match is full")
    
    existing = session.exec(
        select(MatchParticipant).where(
            MatchParticipant.match_id == match_id,
            MatchParticipant.user_id == user_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already joined this match")
    
    session.add(MatchParticipant(
        match_id=match_id,
        user_id=user_id,
        first_name=first_name,
        last_name=last_name
    ))
    match.joined_players += 1
    session.add(match)
    session.commit()
    session.refresh(match)
    return match


@router.delete("/{match_id}", status_code=204) 
def delete_match(match_id:int, request: Request, session: Session = Depends(get_session)):
    user_id, first_name, last_name = require_identity(request)
    match=session.get(Match,match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.organizer_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the organizer can delete this match")
    if match.joined_players != 0:
        raise HTTPException(status_code=400, detail="Cannot delete a match with joined players")
    session.delete(match)
    session.commit()


@router.put("/{match_id}/leave", response_model=MatchRead)
def leave_match(match_id: int, request: Request, session: Session = Depends(get_session)):
    user_id, first_name, last_name = require_identity(request)
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    participant = session.exec(
        select(MatchParticipant).where(
            MatchParticipant.match_id == match_id,
            MatchParticipant.user_id == user_id
        )
    ).first()
    if not participant:
        raise HTTPException(status_code=400, detail="You have not joined this match")
    
    session.delete(participant)
    match.joined_players = max(0, match.joined_players - 1)
    session.add(match)
    session.commit()
    session.refresh(match)
    return match
