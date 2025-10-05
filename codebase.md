

# Project Codebase

## README
## Football Match Finder
A very simple we application that allows users to create, join, and leave games.It solves the problem of finding football games in Madrid, so this app helps players connect, plan, and manage matches with a few clicks.

## Problem Statement:
Many students and local players find it hard to find football games in Madid and find the number of people needed to play and the fields to play at, especially with the language barrier.

So the Football Match Finder solves this problem as i made this simple app that football players can use to:
- Create football matches with location, date, time and maximum number of players
- Join matches and each user can enter each game once
- Leave matches
- Allow organizers that creat that game to delete it only if no one joined that game

## Feature Summary
- First Name and Last Name are stored locally to make sure that a players only joins a game once and you can differentiate between players
- Join match, players can join each game only once
- Leave match, players can leave a game make it empty spot for someone else to join
- Create a match, where the creator of the game can add the date, time, location and maximum numbers of players
- Delete match, only the creator of the game can delete a match only if no one joined
- All data is stored in SQLlite
- Validation is used to prevent duplication or overfilling
- A simple frontend buillt using HTML, CSS,JS

## Project Structure
- static/index.html which is the frontend
- routers/matches.py - matches API
- models.py -SQLModel models
- db.py - engine setup
- main.py - FastAPI app

## How the app works
- First the page stores your first name and last name and creates an id for it in the local storage
- The backened requires three things to create, join and leave which are X-User-Id, X-First-Name, X-Last-Name

## API Endpoints
- GET/matches - list matches
- POST /matches - create matches
- PUT /matches/{id}/join - join match
- PUT /matches/{id}/leave - leave match
- DELETE /matches/{id} - delete match

## Tech Stack
- Backend: FastAPI (Python)
- Database: SQLite (SQLModel)
- Frontend: HTML, CSS, JavaScript

## Tests
- .venv/bin/python3 -m pytest
- pip install pytest pytest-cov
- pytest
- --cov=. 
- --cov-report=term-missing 
- --cov-report=html


## Quickstart
 ```bash
python3 -m venv .venv # creates vm
source .venv/bin/activate # activates vm
pip install -r requirements.txt # install everything this app needs 
uvicorn main:app --reload # use to run the app 







##  Root


###  db.py

py
from sqlmodel import SQLModel, create_engine, Session


engine = create_engine("sqlite:///app.db", echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session



###  main.py

py
from fastapi import FastAPI
from db import create_db_and_tables
from routers.matches import router as matches_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI(title="Football Match Finder")
@app.get("/health") 
def health():
    return {"status":"ok"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(matches_router)


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")





###  models.py

py
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




##  routers


###  matches.py

py
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




##  .pytest_cache



##  .pytest_cache/v



##  .pytest_cache/v/cache



##  tests


###  test_matches.py

py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from main import app
from db import get_session
import models  


@pytest.fixture
def engine():
    # Use shared in-memory SQLite so all connections see the same DB
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s

@pytest.fixture
def client(session):
    def override_get_session():
        try:
            yield session
        finally:
            session.rollback()
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def headers(uid="u1", first="John", last="Doe"):
    return {
        "X-User-Id": uid,
        "X-First-Name": first,
        "X-Last-Name": last,
    }


def test_list_empty(client):
    r = client.get("/matches")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_list(client):
    payload = {"date": "2025-10-04", "time": "18:00:00", "location": "Retiro", "max_players": 10}
    r = client.post("/matches", json=payload, headers=headers("org1", "Alice", "Org"))
    assert r.status_code == 201
    m = r.json()
    assert m["location"] == "Retiro"
    assert m["joined_players"] == 0
    assert m["organizer_user_id"] == "org1"
    assert m["organizer_first_name"] == "Alice"

    r2 = client.get("/matches")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_missing_identity_headers(client):
    payload = {"date": "2025-10-04", "time": "18:00:00", "location": "Retiro", "max_players": 10}
    r = client.post("/matches", json=payload)  # no headers
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing user identity headers"


def test_join_leave_flow(client):
    # Create match
    payload = {"date": "2025-10-04", "time": "18:00:00", "location": "Retiro", "max_players": 3}
    m = client.post("/matches", json=payload, headers=headers("org1")).json()
    mid = m["id"]

    # Join by another user
    r = client.put(f"/matches/{mid}/join", headers=headers("u2", "Bob", "P"))
    assert r.status_code == 200
    assert r.json()["joined_players"] == 1

    # no player should be able to join twice
    r = client.put(f"/matches/{mid}/join", headers=headers("u2", "Bob", "P"))
    assert r.status_code == 400
    assert r.json()["detail"] == "You already joined this match"

    # Leave
    r = client.put(f"/matches/{mid}/leave", headers=headers("u2", "Bob", "P"))
    assert r.status_code == 200
    assert r.json()["joined_players"] == 0

    # you can not leave if you didnt join
    r = client.put(f"/matches/{mid}/leave", headers=headers("u2", "Bob", "P"))
    assert r.status_code == 400
    assert r.json()["detail"] == "You have not joined this match"


def test_match_full(client):
    payload = {"date": "2025-10-04", "time": "18:00:00", "location": "Retiro", "max_players": 1}
    m = client.post("/matches", json=payload, headers=headers("org1")).json()
    mid = m["id"]

    assert client.put(f"/matches/{mid}/join", headers=headers("u2")).status_code == 200
    r = client.put(f"/matches/{mid}/join", headers=headers("u3"))
    assert r.status_code == 400
    assert r.json()["detail"] == "Match is full"


def test_delete_rules(client):
    # Organizer creates
    payload = {"date": "2025-10-04", "time": "18:00:00", "location": "Casa de Campo", "max_players": 5}
    m = client.post("/matches", json=payload, headers=headers("org1", "Alice", "Org")).json()
    mid = m["id"]

    # Non-organizer cannot delete
    r = client.delete(f"/matches/{mid}", headers=headers("u2"))
    assert r.status_code == 403

    # If someone joined, organizer cannot delete
    client.put(f"/matches/{mid}/join", headers=headers("u2"))
    r = client.delete(f"/matches/{mid}", headers=headers("org1"))
    assert r.status_code == 400

    # After leaving, organizer can delete
    client.put(f"/matches/{mid}/leave", headers=headers("u2"))
    r = client.delete(f"/matches/{mid}", headers=headers("org1"))
    assert r.status_code == 204

    # Confirm delete
    r = client.get("/matches")
    assert all(x["id"] != mid for x in r.json())



##  static


###  index.html

html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Football Match Finder</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width: 860px; margin: 24px auto; padding: 0 16px; }
    h1 { margin: 0 0 12px; display:flex; align-items:center; gap:12px; }
    .badge { padding: 2px 10px; border:1px solid #ddd; border-radius:999px; font-size:12px; }
    form, .card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin: 12px 0; }
    input { padding: 8px; margin: 4px 6px 4px 0; }
    button { padding: 8px 12px; border-radius: 8px; border: 1px solid #ccc; cursor: pointer; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
    .muted { color: #666; font-size: 14px; }
    .grid { display: grid; gap: 10px; }
  </style>
</head>
<body>
  <h1>
    Football Match Finder
    <span id="me" class="badge"></span>
  </h1>
  <p class="muted">Create a match, then join, leave, or delete it. Data is stored locally in SQLite.</p>

  
  <form id="create-form">
    <div class="row">
      <input id="date" type="date" required />
      <input id="time" type="time" required />
      <input id="location" placeholder="Location" required />
      <input id="max_players" type="number" min="1" placeholder="Max players" required />
    </div>
    <button type="submit">Create Match</button>
  </form>

  <h2>Matches</h2>
  <div id="matches" class="grid"></div>

  <script>

    function uuid() {
      if (window.crypto?.randomUUID) return crypto.randomUUID();
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random()*16|0, v = c === 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
      });
    }
    function ensureIdentity() {
      let userId = localStorage.getItem('userId');
      let firstName = localStorage.getItem('firstName');
      let lastName = localStorage.getItem('lastName');
      if (!userId) { userId = uuid(); localStorage.setItem('userId', userId); }
      if (!firstName) { firstName = prompt("What's your first name?")?.trim() || 'Guest'; localStorage.setItem('firstName', firstName); }
      if (!lastName) { lastName = prompt("What's your last name?")?.trim() || 'User'; localStorage.setItem('lastName', lastName); }
      document.getElementById('me').textContent = `${firstName} ${lastName}`;
      return { userId, firstName, lastName };
    }
    const me = ensureIdentity();


    function api(path, options = {}) {
      options.headers = Object.assign({
        'X-User-Id': me.userId,
        'X-First-Name': me.firstName,
        'X-Last-Name': me.lastName,
      }, options.headers || {});
      return fetch(path, options);
    }

    
    async function fetchMatches() {
      const res = await api('/matches');
      const data = await res.json();
      renderMatches(data);
    }

    function renderMatches(matches) {
      const box = document.getElementById('matches');
      box.innerHTML = '';
      if (!matches.length) {
        box.innerHTML = '<p class="muted">No matches yet. Create one above.</p>';
        return;
      }
      for (const m of matches) {
        const div = document.createElement('div');
        div.className = 'card';

        const canDelete = (m.organizer_user_id === me.userId) && (m.joined_players === 0);

        div.innerHTML = `
          <strong>#${m.id}</strong> — ${m.date} @ ${m.time} — ${m.location}<br/>
          <span class="muted">${m.joined_players} / ${m.max_players} players</span><br/>
          <span class="muted">Organizer: ${m.organizer_first_name} ${m.organizer_last_name}</span><br/><br/>
          <div class="row">
            <button onclick="joinMatch(${m.id})">Join</button>
            <button onclick="leaveMatch(${m.id})">Leave</button>
            ${canDelete ? `<button onclick="deleteMatch(${m.id})">Delete</button>` : ''}
          </div>
        `;
        box.appendChild(div);
      }
    }

    
    async function joinMatch(id) {
      const res = await api(`/matches/${id}/join`, { method: 'PUT' });
      if (!res.ok) {
        const err = await res.json().catch(()=>({detail:'Unknown error'}));
        alert(err.detail || 'Failed to join');
      }
      fetchMatches();
    }

    async function leaveMatch(id) {
      const res = await api(`/matches/${id}/leave`, { method: 'PUT' });
      if (!res.ok) {
        const err = await res.json().catch(()=>({detail:'Unknown error'}));
        alert(err.detail || 'Failed to leave');
      }
      fetchMatches();
    }

    async function deleteMatch(id) {
      const ok = confirm('Delete this match? (only organizer can delete if 0 joined)');
      if (!ok) return;
      const res = await api(`/matches/${id}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(()=>({detail:'Unknown error'}));
        alert(err.detail || 'Failed to delete');
      }
      fetchMatches();
    }

    
    document.getElementById('create-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const date = document.getElementById('date').value.trim();
      const time = document.getElementById('time').value.trim();
      const location = document.getElementById('location').value.trim();
      const max = parseInt(document.getElementById('max_players').value, 10);
      if (!Number.isInteger(max) || max < 1) {
        alert('Enter a valid number for Max players'); return;
      }
      const payload = { date, time, location, max_players: max, joined_players: 0 };

      const res = await api('/matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const err = await res.json().catch(()=>({detail:'Unknown error'}));
        alert(err.detail || 'Failed to create match');
      } else {
        document.getElementById('date').value = '';
        document.getElementById('time').value = '';
        document.getElementById('location').value = '';
        document.getElementById('max_players').value = '';
      }
      fetchMatches();
    });

    
    fetchMatches();
  </script>
</body>
</html>


