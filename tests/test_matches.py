import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from main import app
from db import get_session
import models  
from conftest import headers


# Fixtures are now in conftest.py - removed duplicate fixtures


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
    r = client.post("/matches", json=payload) 
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing user identity headers"


def test_join_leave_flow(client):
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


def test_health(client):
    """Test the health endpoint"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_match_not_found(client):
    """Test operations on non-existent match"""
    # Try to join non-existent match
    r = client.put("/matches/999/join", headers=headers("u1"))
    assert r.status_code == 404
    assert r.json()["detail"] == "Match not found"
    
    # Try to leave non-existent match
    r = client.put("/matches/999/leave", headers=headers("u1"))
    assert r.status_code == 404
    assert r.json()["detail"] == "Match not found"
    
    # Try to delete non-existent match
    r = client.delete("/matches/999", headers=headers("u1"))
    assert r.status_code == 404
    assert r.json()["detail"] == "Match not found"