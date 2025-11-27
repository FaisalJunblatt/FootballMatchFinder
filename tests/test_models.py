import pytest
from datetime import date, time
from sqlmodel import Session
from models import Match, MatchCreate, MatchRead, MatchParticipant
from sqlalchemy.exc import IntegrityError


def test_match_base_validation():
    """Test basic match model validation"""
    match_data = {
        "date": date(2025, 12, 1),
        "time": time(18, 0),
        "location": "Central Park",
        "max_players": 10,
    }

    match_create = MatchCreate(**match_data)
    assert match_create.date == date(2025, 12, 1)
    assert match_create.time == time(18, 0)
    assert match_create.location == "Central Park"
    assert match_create.max_players == 10
    assert match_create.joined_players == 0  # Default value


def test_match_model_creation():
    """Test full match model with organizer info"""
    match = Match(
        date=date(2025, 12, 1),
        time=time(18, 0),
        location="Central Park",
        max_players=10,
        organizer_user_id="user123",
        organizer_first_name="John",
        organizer_last_name="Doe",
    )

    assert match.organizer_user_id == "user123"
    assert match.organizer_first_name == "John"
    assert match.organizer_last_name == "Doe"


def test_match_read_serialization():
    """Test match read model includes all necessary fields"""
    match_data = {
        "id": 1,
        "date": date(2025, 12, 1),
        "time": time(18, 0),
        "location": "Central Park",
        "max_players": 10,
        "joined_players": 3,
        "organizer_user_id": "user123",
        "organizer_first_name": "John",
        "organizer_last_name": "Doe",
    }

    match_read = MatchRead(**match_data)
    assert match_read.id == 1
    assert match_read.joined_players == 3


def test_match_participant_model():
    """Test match participant model"""
    participant = MatchParticipant(
        match_id=1, user_id="user456", first_name="Jane", last_name="Smith"
    )

    assert participant.match_id == 1
    assert participant.user_id == "user456"
    assert participant.first_name == "Jane"
    assert participant.last_name == "Smith"


def test_match_participant_unique_constraint(session):
    """Test that the same user cannot join the same match twice"""
    # Create a match first
    match = Match(
        date=date(2025, 12, 1),
        time=time(18, 0),
        location="Test Location",
        max_players=10,
        organizer_user_id="org1",
        organizer_first_name="Organizer",
        organizer_last_name="One",
    )
    session.add(match)
    session.commit()
    session.refresh(match)

    # Add first participant
    participant1 = MatchParticipant(
        match_id=match.id, user_id="user1", first_name="John", last_name="Doe"
    )
    session.add(participant1)
    session.commit()

    # Try to add the same user again - should fail
    participant2 = MatchParticipant(
        match_id=match.id,
        user_id="user1",  # Same user
        first_name="John",
        last_name="Doe",
    )
    session.add(participant2)

    with pytest.raises(IntegrityError):
        session.commit()


def test_match_default_values():
    """Test that match models have correct default values"""
    match_create = MatchCreate(
        date=date(2025, 12, 1),
        time=time(18, 0),
        location="Test Location",
        max_players=10,
    )

    assert match_create.joined_players == 0

    match = Match(
        date=date(2025, 12, 1),
        time=time(18, 0),
        location="Test Location",
        max_players=10,
        organizer_user_id="user123",
        organizer_first_name="John",
        organizer_last_name="Doe",
    )

    assert match.joined_players == 0
    assert match.id is None  # Should be None before saving
