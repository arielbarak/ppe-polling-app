import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.connection_manager import manager

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)

@router.websocket("/{poll_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, poll_id: str, user_id: str):
    """
    Handles WebSocket connections and relays messages for the PPE protocol.
    """
    await manager.connect(websocket, poll_id, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # --- PRINT DEBUGGING ---
            print(f"\n[SERVER LOG] Message received from user: {user_id[:10]}...")
            print(f"[SERVER LOG] Raw data: {data}")
            
            message = json.loads(data)
            target_id = message.get("target")
            
            print(f"[SERVER LOG] Parsed message type: {message.get('type')}")
            print(f"[SERVER LOG] Target user ID: {target_id[:10] if target_id else 'None'}")

            if target_id:
                target_ws = manager.active_connections.get(poll_id, {}).get(target_id)
                
                if target_ws:
                    print(f"[SERVER LOG] Target WebSocket found for user {target_id[:10]}...")
                    message["from"] = user_id
                    await target_ws.send_json(message)
                    print(f"[SERVER LOG] Message successfully relayed to target.")
                else:
                    print(f"[SERVER LOG] ERROR: Target WebSocket NOT FOUND for user {target_id[:10]}...")
            else:
                print(f"[SERVER LOG] Message has no target. Not relaying.")

    except WebSocketDisconnect:
        manager.disconnect(poll_id, user_id)
    except json.JSONDecodeError:
        print(f"Received non-JSON message from {user_id[:10]}")
