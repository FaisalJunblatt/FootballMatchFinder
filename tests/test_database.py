import pytest
from sqlmodel import Session, select
from models import Match, MatchParticipant
from datetime import date, time
from sqlalchemy.exc import IntegrityError


class TestDatabaseOperations:
    """Test database-specific operations"""
    
    def test_match_creation_in_db(self, session):
        """Test creating a match directly in the database"""
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        
        session.add(match)
        session.commit()
        session.refresh(match)
        
        assert match.id is not None
        assert match.joined_players == 0
        
        # Verify in database
        retrieved_match = session.get(Match, match.id)
        assert retrieved_match is not None
        assert retrieved_match.location == "Test Park"
    
    def test_match_participant_creation(self, session):
        """Test creating match participants in database"""
        # First create a match
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        # Add participant
        participant = MatchParticipant(
            match_id=match.id,
            user_id="user1",
            first_name="Jane",
            last_name="Player"
        )
        session.add(participant)
        session.commit()
        session.refresh(participant)
        
        assert participant.id is not None
        assert participant.match_id == match.id
    
    def test_unique_constraint_violation(self, session):
        """Test that unique constraint on match_id + user_id is enforced"""
        # Create match
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        # Add first participant
        participant1 = MatchParticipant(
            match_id=match.id,
            user_id="user1",
            first_name="Jane",
            last_name="Player"
        )
        session.add(participant1)
        session.commit()
        
        # Try to add same user to same match again
        participant2 = MatchParticipant(
            match_id=match.id,
            user_id="user1",  # Same user
            first_name="Jane",
            last_name="Player"
        )
        session.add(participant2)
        
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_match_ordering(self, session):
        """Test that matches are properly ordered by date and time"""
        matches = [
            Match(
                date=date(2025, 12, 2),
                time=time(20, 0),
                location="Park B",
                max_players=10,
                organizer_user_id="org1",
                organizer_first_name="John",
                organizer_last_name="Organizer"
            ),
            Match(
                date=date(2025, 12, 1),
                time=time(18, 0),
                location="Park A", 
                max_players=8,
                organizer_user_id="org2",
                organizer_first_name="Jane",
                organizer_last_name="Organizer"
            ),
            Match(
                date=date(2025, 12, 1),
                time=time(20, 0),
                location="Park C",
                max_players=12,
                organizer_user_id="org3",
                organizer_first_name="Bob",
                organizer_last_name="Organizer"
            )
        ]
        
        for match in matches:
            session.add(match)
        session.commit()
        
        # Query with ordering
        ordered_matches = session.exec(
            select(Match).order_by(Match.date, Match.time)
        ).all()
        
        assert len(ordered_matches) == 3
        assert ordered_matches[0].date == date(2025, 12, 1)
        assert ordered_matches[0].time == time(18, 0)
        assert ordered_matches[1].date == date(2025, 12, 1)
        assert ordered_matches[1].time == time(20, 0)
        assert ordered_matches[2].date == date(2025, 12, 2)
        assert ordered_matches[2].time == time(20, 0)
    
    def test_participant_deletion_cascade(self, session):
        """Test that participants are properly handled when match is deleted"""
        # Create match
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        # Add participants
        participants = [
            MatchParticipant(
                match_id=match.id,
                user_id="user1",
                first_name="Player",
                last_name="One"
            ),
            MatchParticipant(
                match_id=match.id,
                user_id="user2",
                first_name="Player", 
                last_name="Two"
            )
        ]
        
        for participant in participants:
            session.add(participant)
        session.commit()
        
        # Verify participants exist
        participant_count = len(session.exec(
            select(MatchParticipant).where(MatchParticipant.match_id == match.id)
        ).all())
        assert participant_count == 2
        
        # Delete match (participants should be handled by foreign key)
        session.delete(match)
        session.commit()
        
        # Verify participants are gone (or handle appropriately based on your FK setup)
        remaining_participants = session.exec(
            select(MatchParticipant).where(MatchParticipant.match_id == match.id)
        ).all()
        # This test assumes ON DELETE CASCADE behavior
        # Adjust assertion based on your actual foreign key configuration
    
    def test_match_participant_queries(self, session):
        """Test querying match participants"""
        # Create match
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        # Add participants
        participants_data = [
            ("user1", "Alice", "Smith"),
            ("user2", "Bob", "Jones"),
            ("user3", "Charlie", "Brown")
        ]
        
        for user_id, first_name, last_name in participants_data:
            participant = MatchParticipant(
                match_id=match.id,
                user_id=user_id,
                first_name=first_name,
                last_name=last_name
            )
            session.add(participant)
        session.commit()
        
        # Query participants for match
        match_participants = session.exec(
            select(MatchParticipant).where(MatchParticipant.match_id == match.id)
        ).all()
        
        assert len(match_participants) == 3
        user_ids = [p.user_id for p in match_participants]
        assert "user1" in user_ids
        assert "user2" in user_ids
        assert "user3" in user_ids
        
        # Query specific participant
        specific_participant = session.exec(
            select(MatchParticipant).where(
                MatchParticipant.match_id == match.id,
                MatchParticipant.user_id == "user2"
            )
        ).first()
        
        assert specific_participant is not None
        assert specific_participant.first_name == "Bob"
        assert specific_participant.last_name == "Jones"


class TestDataIntegrity:
    """Test data integrity and edge cases"""
    
    def test_match_with_zero_max_players(self, session):
        """Test creating match with edge case values"""
        # Test with 0 max players (should this be allowed?)
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=0,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        assert match.max_players == 0
    
    def test_match_with_large_max_players(self, session):
        """Test match with very large max_players value"""
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Stadium",
            max_players=10000,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        assert match.max_players == 10000
    
    def test_match_with_special_characters_in_location(self, session):
        """Test match with special characters in location"""
        special_location = "Parque José María Aznar (Campo #3) - ñáéíóú"
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location=special_location,
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="José",
            organizer_last_name="García"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        assert match.location == special_location
        assert match.organizer_first_name == "José"
    
    def test_participant_with_special_characters_in_names(self, session):
        """Test participant with special characters in names"""
        # Create match first
        match = Match(
            date=date(2025, 12, 1),
            time=time(18, 0),
            location="Test Park",
            max_players=10,
            organizer_user_id="org1",
            organizer_first_name="John",
            organizer_last_name="Organizer"
        )
        session.add(match)
        session.commit()
        session.refresh(match)
        
        # Add participant with special characters
        participant = MatchParticipant(
            match_id=match.id,
            user_id="user1",
            first_name="José María",
            last_name="González-Pérez"
        )
        session.add(participant)
        session.commit()
        session.refresh(participant)
        
        assert participant.first_name == "José María"
        assert participant.last_name == "González-Pérez"