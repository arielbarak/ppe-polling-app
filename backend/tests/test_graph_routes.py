"""
Tests for graph API routes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.poll_service import poll_service
from app.models.poll import PollCreate


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_poll(client):
    """Create a sample poll with registrants."""
    # Create poll
    response = client.post(
        "/polls/",
        json={
            "question": "Test Poll",
            "options": ["Option 1", "Option 2"]
        }
    )
    poll = response.json()
    poll_id = poll["id"]
    
    # Register multiple users
    for i in range(5):
        client.post(
            f"/polls/{poll_id}/register",
            json={
                "kty": "EC",
                "crv": "P-256",
                "x": f"test_x_{i}",
                "y": f"test_y_{i}"
            }
        )
    
    return poll_id


def test_generate_graph(client, sample_poll):
    """Test graph generation endpoint."""
    response = client.get(f"/polls/{sample_poll}/graph/generate")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "properties" in data
    assert "metrics" in data
    assert data["num_participants"] == 5


def test_generate_graph_invalid_poll(client):
    """Test graph generation with invalid poll."""
    response = client.get("/polls/invalid-poll-id/graph/generate")
    assert response.status_code == 404


def test_generate_graph_insufficient_participants(client):
    """Test graph generation with too few participants."""
    # Create poll with only 1 registrant
    response = client.post(
        "/polls/",
        json={
            "question": "Test Poll",
            "options": ["Option 1", "Option 2"]
        }
    )
    poll_id = response.json()["id"]
    
    client.post(
        f"/polls/{poll_id}/register",
        json={"kty": "EC", "crv": "P-256", "x": "test_x", "y": "test_y"}
    )
    
    response = client.get(f"/polls/{poll_id}/graph/generate")
    assert response.status_code == 400


def test_get_neighbors(client, sample_poll):
    """Test getting user neighbors."""
    # First generate the graph
    client.get(f"/polls/{sample_poll}/graph/generate")
    
    # Get poll to find a user ID
    response = client.get(f"/polls/{sample_poll}")
    poll = response.json()
    user_id = list(poll["registrants"].keys())[0]
    
    # Get neighbors
    response = client.get(
        f"/polls/{sample_poll}/graph/neighbors",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "neighbors" in data
    assert "neighbor_count" in data
    assert isinstance(data["neighbors"], list)


def test_get_full_graph(client, sample_poll):
    """Test getting complete graph."""
    response = client.get(f"/polls/{sample_poll}/graph/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "graph" in data
    assert "properties" in data
    assert len(data["graph"]) == 5  # 5 registered users


def test_invalidate_graph(client, sample_poll):
    """Test graph invalidation."""
    # Generate graph first
    client.get(f"/polls/{sample_poll}/graph/generate")
    
    # Invalidate
    response = client.post(f"/polls/{sample_poll}/graph/invalidate")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Graph invalidated successfully"