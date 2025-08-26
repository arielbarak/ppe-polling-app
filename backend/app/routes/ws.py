import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.connection_manager import manager

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)

@router.websocket("/{poll_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, poll_id: str, client_id: str):
    """
    Handles WebSocket connections and relays messages for the PPE protocol.
    """
    await manager.connect(websocket, poll_id, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # --- PRINT DEBUGGING ---
            print(f"\n[SERVER LOG] Message received from user: {client_id[:10]}...")
            print(f"[SERVER LOG] Raw data: {data}")
            
            target_id = message.get("target")
            
            print(f"[SERVER LOG] Parsed message type: {message.get('type')}")
            print(f"[SERVER LOG] Target user ID: {target_id[:10] if target_id else 'None'}")

            if target_id:
                target_ws = manager.active_connections.get(poll_id, {}).get(target_id)
                
                if target_ws:
                    print(f"[SERVER LOG] Target WebSocket found for user {target_id[:10]}...")
                    message["from"] = client_id
                    await target_ws.send_json(message)
                    print(f"[SERVER LOG] Message successfully relayed to target.")
                else:
                    print(f"[SERVER LOG] ERROR: Target WebSocket NOT FOUND for user {target_id[:10]}...")
            else:
                print(f"[SERVER LOG] Message has no target. Not relaying.")

            if message["type"] == "request_verification":
                # Broadcast verification request to target user
                await manager.send_personal_message(
                    json.dumps({
                        "type": "verification_requested",
                        "from": client_id
                    }),
                    poll_id,
                    message["target"]
                )
            
            elif message["type"] == "accept_verification":
                # Broadcast verification acceptance
                await manager.broadcast_to_poll(
                    json.dumps({
                        "type": "verification_accepted",
                        "verifier": client_id,
                        "verified": message["target"]
                    }),
                    poll_id
                )
    except WebSocketDisconnect:
        manager.disconnect(poll_id, client_id)
    except json.JSONDecodeError:
        print(f"Received non-JSON message from {client_id[:10]}")
