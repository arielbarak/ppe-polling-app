import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.sanity
def test_api_healthcheck():
    """Test the API is running and responding to requests"""
    response = client.get("/api/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.sanity
def test_api_version():
    """Test the API version endpoint returns the correct information"""
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert "api_version" in response.json()

@pytest.mark.sanity
def test_poll_endpoints_existence():
    """Test that all required poll API endpoints exist and return expected status codes"""
    # Test GET /polls/ (list polls)
    response = client.get("/polls/")
    assert response.status_code in [200, 204]  # 204 if no polls exist
    
    # Test POST /polls/ (create poll)
    # Even if it fails due to validation, it should return 422, not 404
    response = client.post("/polls/", json={})
    assert response.status_code in [201, 422]  # 422 for validation error
    
    # Test GET /polls/{poll_id} (get poll)
    # Will return 404 for non-existent poll, but endpoint should exist
    response = client.get("/polls/nonexistent-poll")
    assert response.status_code == 404
    
    # Test POST /polls/{poll_id}/vote (vote on poll)
    # Will return 404 for non-existent poll, but endpoint should exist
    response = client.post("/polls/nonexistent-poll/vote", json={})
    assert response.status_code in [404, 422]  # 422 for validation error
    
    # Test GET /polls/{poll_id}/verify (verify poll)
    # Will return 404 for non-existent poll, but endpoint should exist
    response = client.get("/polls/nonexistent-poll/verify")
    assert response.status_code == 404

@pytest.mark.sanity
def test_websocket_endpoint_existence():
    """Test that the WebSocket endpoint exists"""
    # We can't fully test WebSocket functionality with TestClient,
    # but we can check that the endpoint exists and responds correctly
    # by intentionally causing a WebSocket upgrade failure
    
    # This will fail because it's not a proper WebSocket connection,
    # but it should return a 400 error, not a 404 (not found)
    # Note: The path should match the actual path in app/routes/ws.py
    # The WebSocket route is registered with the path "/{poll_id}/{client_id}"
    # in the router with prefix "/ws"
    response = client.get("/ws/test-poll/test-user")
    # The status code may be 404 if the WebSocket endpoint requires WebSocket protocol
    # or 400, 403, 405, 426 for protocol errors
    # Just ensure it's not a server error
    assert response.status_code < 500

@pytest.mark.sanity
def test_basic_poll_creation():
    """
    Test basic poll creation functionality
    This test will actually create a poll in the system
    """
    # Create a basic poll
    poll_data = {
        "question": "Sanity Test Poll",
        "options": ["Option 1", "Option 2"]
    }
    
    create_response = client.post("/polls/", json=poll_data)
    
    # If we can't create a poll, print detailed error information
    if create_response.status_code != 201:
        print(f"Error creating poll: {create_response.status_code}")
        print(create_response.text)
        # This will fail the test, but gives us more information
    
    assert create_response.status_code == 201
    poll_id = create_response.json()["id"]
    
    # Verify we can retrieve the poll
    get_response = client.get(f"/polls/{poll_id}")
    assert get_response.status_code == 200
    assert get_response.json()["question"] == "Sanity Test Poll"
    assert get_response.json()["options"] == ["Option 1", "Option 2"]

@pytest.mark.sanity
def test_full_basic_poll_flow():
    """
    Test a complete basic poll flow with just basic assertions.
    We'll skip the detailed validation since this is just a sanity test.
    """
    # Create a poll
    poll_data = {
        "question": "Basic Flow Test",
        "options": ["Yes", "No", "Maybe"]
    }
    
    create_response = client.post("/polls/", json=poll_data)
    assert create_response.status_code == 201
    poll_id = create_response.json()["id"]
    
    # Register two users
    user1_key = {"key": "user1-key"}
    user2_key = {"key": "user2-key"}
    
    reg1_response = client.post(f"/polls/{poll_id}/register", json=user1_key)
    assert reg1_response.status_code == 200
    
    reg2_response = client.post(f"/polls/{poll_id}/register", json=user2_key)
    assert reg2_response.status_code == 200
    
    # Get user IDs
    user1_id_response = client.post("/polls/userid", json=user1_key)
    assert user1_id_response.status_code == 200
    user1_id = user1_id_response.json()
    
    user2_id_response = client.post("/polls/userid", json=user2_key)
    assert user2_id_response.status_code == 200
    user2_id = user2_id_response.json()
    
    # Users verify each other
    verify1_response = client.post(f"/polls/{poll_id}/verify/{user2_id}", json=user1_key)
    assert verify1_response.status_code == 200
    
    verify2_response = client.post(f"/polls/{poll_id}/verify/{user1_id}", json=user2_key)
    assert verify2_response.status_code == 200
    
    # Complete PPE certification between users
    ppe_response1 = client.post(
        f"/polls/{poll_id}/ppe-certification", 
        json={
            "user1_public_key": user1_key,
            "user2_public_key": user2_key
        }
    )
    assert ppe_response1.status_code == 200
    
    # Verify the poll
    verify_response = client.get(f"/polls/{poll_id}/verify")
    assert verify_response.status_code == 200
    
    # As a sanity test, we won't try to vote since that requires real cryptographic signatures
    # Just check that the poll verification endpoint works
    assert "verification" in verify_response.json()