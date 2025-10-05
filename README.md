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



