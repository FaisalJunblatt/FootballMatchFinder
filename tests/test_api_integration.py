import pytest
from datetime import date, time, datetime, timedelta
from conftest import headers


class TestMatchCreation:
    """Test match creation scenarios"""
    
    def test_create_match_with_all_fields(self, client):
        """Test creating a match with all required fields"""
        payload = {
            "date": "2025-12-01",
            "time": "18:00:00",
            "location": "Central Park",
            "max_players": 10
        }
        
        response = client.post("/matches", json=payload, headers=headers("org1", "John", "Organizer"))
        assert response.status_code == 201
        
        match = response.json()
        assert match["date"] == "2025-12-01"
        assert match["time"] == "18:00:00"
        assert match["location"] == "Central Park"
        assert match["max_players"] == 10
        assert match["joined_players"] == 0
        assert match["organizer_user_id"] == "org1"
        assert match["organizer_first_name"] == "John"
        assert match["organizer_last_name"] == "Organizer"
        assert "id" in match

    def test_create_match_invalid_data(self, client):
        """Test creating match with invalid data"""
        # Missing required fields
        payload = {"location": "Park"}
        response = client.post("/matches", json=payload, headers=headers())
        assert response.status_code == 422
        
        # Invalid date format
        payload = {
            "date": "invalid-date",
            "time": "18:00:00",
            "location": "Park",
            "max_players": 10
        }
        response = client.post("/matches", json=payload, headers=headers())
        assert response.status_code == 422
        
        # Invalid time format
        payload = {
            "date": "2025-12-01",
            "time": "invalid-time",
            "location": "Park", 
            "max_players": 10
        }
        response = client.post("/matches", json=payload, headers=headers())
        assert response.status_code == 422

    def test_create_match_boundary_values(self, client):
        """Test creating matches with boundary values"""
        # Minimum players
        payload = {
            "date": "2025-12-01",
            "time": "18:00:00",
            "location": "Park",
            "max_players": 1
        }
        response = client.post("/matches", json=payload, headers=headers())
        assert response.status_code == 201
        
        # Large number of players
        payload = {
            "date": "2025-12-01", 
            "time": "18:00:00",
            "location": "Stadium",
            "max_players": 100
        }
        response = client.post("/matches", json=payload, headers=headers())
        assert response.status_code == 201


class TestMatchListing:
    """Test match listing functionality"""
    
    def test_list_matches_empty(self, client):
        """Test listing when no matches exist"""
        response = client.get("/matches")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_matches_ordering(self, client):
        """Test that matches are ordered by date and time"""
        # Create matches in different order
        matches_data = [
            {"date": "2025-12-02", "time": "20:00:00", "location": "Park B", "max_players": 10},
            {"date": "2025-12-01", "time": "18:00:00", "location": "Park A", "max_players": 8},
            {"date": "2025-12-01", "time": "20:00:00", "location": "Park C", "max_players": 12},
        ]
        
        for match_data in matches_data:
            client.post("/matches", json=match_data, headers=headers())
        
        response = client.get("/matches")
        assert response.status_code == 200
        
        matches = response.json()
        assert len(matches) == 3
        
        # Should be ordered by date, then time
        assert matches[0]["date"] == "2025-12-01" and matches[0]["time"] == "18:00:00"
        assert matches[1]["date"] == "2025-12-01" and matches[1]["time"] == "20:00:00"
        assert matches[2]["date"] == "2025-12-02" and matches[2]["time"] == "20:00:00"


class TestMatchJoining:
    """Test match joining functionality"""
    
    def test_join_match_success(self, client):
        """Test successfully joining a match"""
        # Create match
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        # Join match
        response = client.put(f"/matches/{match['id']}/join", headers=headers("user1", "John", "Player"))
        assert response.status_code == 200
        
        updated_match = response.json()
        assert updated_match["joined_players"] == 1
        assert updated_match["id"] == match["id"]
    
    def test_join_match_twice_fails(self, client):
        """Test that joining the same match twice fails"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        # Join once - success
        response = client.put(f"/matches/{match['id']}/join", headers=headers("user1"))
        assert response.status_code == 200
        
        # Join again - should fail
        response = client.put(f"/matches/{match['id']}/join", headers=headers("user1"))
        assert response.status_code == 400
        assert "already joined" in response.json()["detail"]
    
    def test_join_full_match_fails(self, client):
        """Test joining a full match fails"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 1}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        # Fill the match
        response = client.put(f"/matches/{match['id']}/join", headers=headers("user1"))
        assert response.status_code == 200
        
        # Try to join when full
        response = client.put(f"/matches/{match['id']}/join", headers=headers("user2"))
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestMatchLeaving:
    """Test match leaving functionality"""
    
    def test_leave_match_success(self, client):
        """Test successfully leaving a match"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        # Join then leave
        client.put(f"/matches/{match['id']}/join", headers=headers("user1"))
        response = client.put(f"/matches/{match['id']}/leave", headers=headers("user1"))
        
        assert response.status_code == 200
        updated_match = response.json()
        assert updated_match["joined_players"] == 0
    
    def test_leave_match_not_joined_fails(self, client):
        """Test leaving a match you haven't joined fails"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        response = client.put(f"/matches/{match['id']}/leave", headers=headers("user1"))
        assert response.status_code == 400
        assert "not joined" in response.json()["detail"]


class TestMatchDeletion:
    """Test match deletion functionality"""
    
    def test_delete_match_by_organizer(self, client):
        """Test organizer can delete empty match"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        response = client.delete(f"/matches/{match['id']}", headers=headers("org1"))
        assert response.status_code == 204
        
        # Verify deletion
        matches = client.get("/matches").json()
        assert not any(m["id"] == match["id"] for m in matches)
    
    def test_delete_match_non_organizer_fails(self, client):
        """Test non-organizer cannot delete match"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        response = client.delete(f"/matches/{match['id']}", headers=headers("user1"))
        assert response.status_code == 403
        assert "organizer" in response.json()["detail"]
    
    def test_delete_match_with_players_fails(self, client):
        """Test cannot delete match with joined players"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        match = client.post("/matches", json=payload, headers=headers("org1")).json()
        
        # Add player
        client.put(f"/matches/{match['id']}/join", headers=headers("user1"))
        
        # Try to delete
        response = client.delete(f"/matches/{match['id']}", headers=headers("org1"))
        assert response.status_code == 400
        assert "joined players" in response.json()["detail"]


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization scenarios"""
    
    def test_missing_user_id_header(self, client):
        """Test requests without user ID header fail"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        
        headers_no_user = {"X-First-Name": "John", "X-Last-Name": "Doe"}
        response = client.post("/matches", json=payload, headers=headers_no_user)
        assert response.status_code == 401
    
    def test_missing_name_headers(self, client):
        """Test requests without name headers fail"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        
        headers_no_name = {"X-User-Id": "user1"}
        response = client.post("/matches", json=payload, headers=headers_no_name)
        assert response.status_code == 401
    
    def test_alternative_name_headers(self, client):
        """Test that alternative name header formats work"""
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 5}
        
        alt_headers = {
            "X-User-Id": "user1",
            "X-User-First-Name": "John",
            "X-User-Last-Name": "Doe"
        }
        response = client.post("/matches", json=payload, headers=alt_headers)
        assert response.status_code == 201


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_nonexistent_match_operations(self, client):
        """Test operations on non-existent matches"""
        non_existent_id = 99999
        
        # Join non-existent match
        response = client.put(f"/matches/{non_existent_id}/join", headers=headers("user1"))
        assert response.status_code == 404
        
        # Leave non-existent match
        response = client.put(f"/matches/{non_existent_id}/leave", headers=headers("user1"))
        assert response.status_code == 404
        
        # Delete non-existent match
        response = client.delete(f"/matches/{non_existent_id}", headers=headers("user1"))
        assert response.status_code == 404
    
    def test_invalid_match_id_format(self, client):
        """Test operations with invalid match ID format"""
        invalid_id = "not-a-number"
        
        response = client.put(f"/matches/{invalid_id}/join", headers=headers("user1"))
        assert response.status_code == 422


class TestComplexScenarios:
    """Test complex multi-step scenarios"""
    
    def test_full_match_lifecycle(self, client):
        """Test complete match lifecycle"""
        # Create match
        payload = {"date": "2025-12-01", "time": "18:00:00", "location": "Park", "max_players": 3}
        match = client.post("/matches", json=payload, headers=headers("org1", "Organizer", "One")).json()
        
        # Multiple users join
        client.put(f"/matches/{match['id']}/join", headers=headers("user1", "Player", "One"))
        client.put(f"/matches/{match['id']}/join", headers=headers("user2", "Player", "Two"))
        
        # Check match is updated
        matches = client.get("/matches").json()
        updated_match = next(m for m in matches if m["id"] == match["id"])
        assert updated_match["joined_players"] == 2
        
        # One player leaves
        client.put(f"/matches/{match['id']}/leave", headers=headers("user1"))
        
        # Check updated count
        matches = client.get("/matches").json()
        updated_match = next(m for m in matches if m["id"] == match["id"])
        assert updated_match["joined_players"] == 1
        
        # Last player leaves, then organizer can delete
        client.put(f"/matches/{match['id']}/leave", headers=headers("user2"))
        response = client.delete(f"/matches/{match['id']}", headers=headers("org1"))
        assert response.status_code == 204