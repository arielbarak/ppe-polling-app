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
            
            # Validate required message fields
            if not isinstance(message, dict):
                await websocket.send_json({
                    "type": "error",
                    "error": "invalid_message",
                    "message": "Message must be a JSON object."
                })
                continue
                
            if "type" not in message:
                await websocket.send_json({
                    "type": "error",
                    "error": "missing_type",
                    "message": "Message must include a 'type' field."
                })
                continue
                
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
                    # Send error message back to sender
                    await websocket.send_json({
                        "type": "error",
                        "error": "target_offline",
                        "message": "The user you are trying to reach is offline or not available.",
                        "target": target_id
                    })
            else:
                print(f"[SERVER LOG] Message has no target. Not relaying.")
                await websocket.send_json({
                    "type": "error",
                    "error": "no_target",
                    "message": "The message must specify a target user."
                })

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
        print(f"[SERVER LOG] Client {client_id[:10]} disconnected.")
    except json.JSONDecodeError:
        print(f"[SERVER LOG] Received non-JSON message from {client_id[:10]}")
        await websocket.send_json({
            "type": "error",
            "error": "invalid_format",
            "message": "Invalid message format. Messages must be valid JSON."
        })
