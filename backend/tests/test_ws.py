import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app.main import app
from app.services.connection_manager import ConnectionManager

client = TestClient(app)

@pytest.fixture
def mock_connection_manager():
    """Create a mock connection manager for WebSocket testing.
    
    This fixture provides a mock of the connection manager used in WebSocket
    tests, with all necessary methods mocked for testing WebSocket connections.
    
    Returns:
        MagicMock: A configured mock of the connection manager.
    """
    with patch('app.routes.ws.manager') as mock_manager:
        # Create a mock for the ConnectionManager
        mock_manager.active_connections = {}
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_manager.broadcast_to_poll = AsyncMock()
        mock_manager.send_personal_message = AsyncMock()
        yield mock_manager

@pytest.fixture
def mock_poll_service():
    """Create a mock poll service for WebSocket testing.
    
    This fixture provides a mock of the poll service with a test poll
    configured for WebSocket connection tests.
    
    Returns:
        MagicMock: A configured mock of the poll service.
    """
    with patch('app.services.poll_service') as mock_service:
        poll = MagicMock()
        poll.id = "test-poll-id"
        poll.question = "Test Question"
        poll.options = ["Option 1", "Option 2"]
        mock_service.get_poll.return_value = poll
        yield mock_service

@pytest.mark.asyncio
async def test_websocket_connect():
    """Test WebSocket connection establishment.
    
    This test validates that a WebSocket connection can be established
    successfully and the connection manager's connect method is called
    with the correct parameters.
    
    The test bypasses the TestClient and directly tests the WebSocket 
    handler for more precise testing of the connection mechanism.
    
    Returns:
        None
    
    Raises:
        AssertionError: If the connection manager's connect method is not called correctly.
    """
    # This is a special test that directly tests the WebSocket handler
    # rather than using the TestClient, which can't fully test WebSockets
    
    # Setup mocks
    from app.routes.ws import websocket_endpoint
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    poll_id = "test-poll-id"
    client_id = "test-client-id"
    
    # Mock connection manager
    with patch('app.routes.ws.manager') as mock_manager:
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_manager.broadcast_to_poll = AsyncMock()
        mock_manager.send_personal_message = AsyncMock()
        
        # Setup WebSocket to raise an exception after the first message
        websocket.receive_text = AsyncMock(side_effect=["message", Exception("Test disconnect")])
        
        # Call the websocket endpoint directly
        try:
            await websocket_endpoint(websocket, poll_id, client_id)
        except Exception:
            pass  # Expected exception from the mock
        
        # Verify connection was established
        mock_manager.connect.assert_called_once_with(websocket, poll_id, client_id)

@pytest.mark.asyncio
async def test_websocket_disconnect():
    """Test WebSocket disconnection handling.
    
    This test validates that when a WebSocket disconnection occurs, the
    connection manager's disconnect method is called correctly to clean up
    the connection resources.
    
    The test simulates a WebSocketDisconnect exception and verifies
    that the disconnect handler is invoked with the correct parameters.
    
    Returns:
        None
    
    Raises:
        AssertionError: If the connection manager's disconnect method is not called correctly.
    """
    # Setup mocks
    from app.routes.ws import websocket_endpoint
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    poll_id = "test-poll-id"
    client_id = "test-client-id"
    
    # Mock connection manager
    with patch('app.routes.ws.manager') as mock_manager:
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        
        # Setup WebSocket to raise a WebSocketDisconnect exception
        from fastapi import WebSocketDisconnect
        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))
        
        # Call the websocket endpoint directly
        await websocket_endpoint(websocket, poll_id, client_id)
        
        # Verify disconnect was handled
        mock_manager.disconnect.assert_called_once_with(poll_id, client_id)

@pytest.mark.asyncio
async def test_connection_manager_methods():
    """Test the core functionality of the ConnectionManager class.
    
    This test validates the complete lifecycle of a WebSocket connection through
    the ConnectionManager, including:
    
    1. Connecting a client to a poll
    2. Sending personal messages to a client
    3. Broadcasting messages to all clients in a poll
    4. Disconnecting a client from a poll
    
    The test verifies that connections are properly stored and messages are
    correctly sent to the intended recipients.
    
    Returns:
        None
    
    Raises:
        AssertionError: If any of the connection manager operations don't behave as expected.
    """
    manager = ConnectionManager()
    
    # Create mock WebSocket
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    
    # Test connect
    poll_id = "test-poll-id"
    user_id = "test-user-id"
    await manager.connect(websocket, poll_id, user_id)
    
    # Verify connection is in active_connections
    assert poll_id in manager.active_connections
    assert user_id in manager.active_connections[poll_id]
    assert manager.active_connections[poll_id][user_id] == websocket
    
    # Test send_personal_message
    message = "Test message"
    await manager.send_personal_message(message, websocket)
    websocket.send_text.assert_called_with(message)
    
    # Test broadcast_to_poll
    broadcast_message = "Broadcast message"
    await manager.broadcast_to_poll(broadcast_message, poll_id)
    websocket.send_text.assert_called_with(broadcast_message)
    
    # Test disconnect
    manager.disconnect(poll_id, user_id)
    assert user_id not in manager.active_connections[poll_id]