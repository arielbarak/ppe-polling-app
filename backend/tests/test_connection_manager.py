import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import json
from app.services.connection_manager import ConnectionManager

@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for testing.
    
    Returns:
        ConnectionManager: A new instance of the ConnectionManager class.
    """
    return ConnectionManager()

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing connection operations.
    
    Returns:
        AsyncMock: A mock WebSocket with async methods for testing.
    """
    mock = AsyncMock()
    mock.send_text = AsyncMock()
    mock.accept = AsyncMock()
    return mock

def test_connection_manager_initialization(connection_manager):
    """Test that the ConnectionManager initializes with an empty connections dictionary.
    
    This test verifies that a new ConnectionManager starts with no active connections.
    
    Args:
        connection_manager: A fixture that provides a new ConnectionManager instance.
        
    Returns:
        None
        
    Raises:
        AssertionError: If the active_connections dictionary is not empty.
    """
    assert connection_manager.active_connections == {}

@pytest.mark.asyncio
async def test_connect(connection_manager, mock_websocket):
    """Test connecting a user to a poll in the ConnectionManager.
    
    This test verifies that the connect method:
    1. Properly adds the WebSocket connection to the active_connections dictionary
    2. Organizes connections by poll_id and user_id
    3. Calls the WebSocket accept method to establish the connection
    
    Args:
        connection_manager: A fixture providing a ConnectionManager instance.
        mock_websocket: A fixture providing a mock WebSocket.
        
    Returns:
        None
        
    Raises:
        AssertionError: If the connection isn't properly established or stored.
    """
    poll_id = "test-poll-id"
    user_id = "test-user-id"
    
    # Connect a user
    await connection_manager.connect(mock_websocket, poll_id, user_id)
    
    # Verify the connection was added
    assert poll_id in connection_manager.active_connections
    assert user_id in connection_manager.active_connections[poll_id]
    assert connection_manager.active_connections[poll_id][user_id] == mock_websocket
    
    # Verify accept was called
    mock_websocket.accept.assert_called_once()

@pytest.mark.asyncio
async def test_connect_multiple_users_to_poll(connection_manager):
    """Test connecting multiple users to the same poll.
    
    This test verifies that the ConnectionManager can handle multiple users
    connecting to the same poll while maintaining separate connections for each user.
    
    Args:
        connection_manager: A fixture providing a ConnectionManager instance.
        
    Returns:
        None
        
    Raises:
        AssertionError: If multiple connections aren't properly managed.
    """
    poll_id = "test-poll-id"
    
    # Create mock connections
    websocket1 = AsyncMock()
    websocket1.accept = AsyncMock()
    websocket2 = AsyncMock()
    websocket2.accept = AsyncMock()
    
    # Connect users
    await connection_manager.connect(websocket1, poll_id, "user1")
    await connection_manager.connect(websocket2, poll_id, "user2")
    
    # Verify both connections were added
    assert len(connection_manager.active_connections[poll_id]) == 2
    assert "user1" in connection_manager.active_connections[poll_id]
    assert "user2" in connection_manager.active_connections[poll_id]
    assert connection_manager.active_connections[poll_id]["user1"] == websocket1
    assert connection_manager.active_connections[poll_id]["user2"] == websocket2

def test_disconnect(connection_manager):
    """Test disconnecting a user from a poll"""
    poll_id = "test-poll-id"
    
    # Setup connections in the manager directly
    connection_manager.active_connections[poll_id] = {
        "user1": AsyncMock(),
        "user2": AsyncMock()
    }
    
    # Disconnect one user
    connection_manager.disconnect(poll_id, "user1")
    
    # Verify only one connection remains
    assert len(connection_manager.active_connections[poll_id]) == 1
    assert "user1" not in connection_manager.active_connections[poll_id]
    assert "user2" in connection_manager.active_connections[poll_id]

def test_disconnect_last_user_from_poll(connection_manager):
    """Test disconnecting the last user from a poll removes the poll entry"""
    poll_id = "test-poll-id"
    
    # Setup a single connection
    connection_manager.active_connections[poll_id] = {
        "user1": AsyncMock()
    }
    
    # Disconnect the user
    connection_manager.disconnect(poll_id, "user1")
    
    # The poll should still exist with empty connections
    assert poll_id in connection_manager.active_connections
    assert len(connection_manager.active_connections[poll_id]) == 0

def test_disconnect_from_nonexistent_poll(connection_manager):
    """Test disconnecting from a poll that doesn't exist"""
    # This should not raise an exception
    connection_manager.disconnect("nonexistent-poll", "user1")
    # No assertion needed - we're just checking it doesn't raise an exception

@pytest.mark.asyncio
async def test_broadcast_to_poll(connection_manager):
    """Test broadcasting a message to a poll"""
    poll_id = "test-poll-id"
    
    # Create mock connections
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    
    # Setup connections directly
    connection_manager.active_connections[poll_id] = {
        "user1": websocket1,
        "user2": websocket2
    }
    
    # Broadcast a message
    message = json.dumps({"type": "update", "data": "test"})
    await connection_manager.broadcast_to_poll(message, poll_id)
    
    # Verify both connections received the message
    websocket1.send_text.assert_called_once_with(message)
    websocket2.send_text.assert_called_once_with(message)

@pytest.mark.asyncio
async def test_broadcast_to_nonexistent_poll(connection_manager):
    """Test broadcasting to a poll that doesn't exist"""
    # This should not raise an exception
    await connection_manager.broadcast_to_poll("test", "nonexistent-poll")

@pytest.mark.asyncio
async def test_send_personal_message(connection_manager, mock_websocket):
    """Test sending a personal message to a WebSocket"""
    message = "Hello, this is a personal message"
    await connection_manager.send_personal_message(message, mock_websocket)
    mock_websocket.send_text.assert_called_once_with(message)