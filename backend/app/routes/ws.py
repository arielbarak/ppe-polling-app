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
    
    Enhanced to support full symmetric CAPTCHA PPE protocol.
    """
    await manager.connect(websocket, poll_id, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            print(f"\n[SERVER LOG] Message from {client_id[:10]}...: {message.get('type')}")
            
            # Validate message structure
            if not isinstance(message, dict) or "type" not in message:
                await websocket.send_json({
                    "type": "error",
                    "error": "invalid_message",
                    "message": "Message must be a JSON object with 'type' field."
                })
                continue
            
            msg_type = message.get("type")
            target_id = message.get("target")
            
            # Handle PPE-specific messages
            if msg_type in ["ppe_challenge", "ppe_commitment", "ppe_reveal", "ppe_signature", "ppe_complete"]:
                if not target_id:
                    await websocket.send_json({
                        "type": "error",
                        "error": "no_target",
                        "message": "PPE messages must specify a target user."
                    })
                    continue
                
                # Find target websocket
                target_ws = manager.active_connections.get(poll_id, {}).get(target_id)
                
                if target_ws:
                    # Relay message to target with sender info
                    message["from"] = client_id
                    await target_ws.send_json(message)
                    print(f"[SERVER LOG] Relayed {msg_type} to {target_id[:10]}...")
                else:
                    print(f"[SERVER LOG] Target {target_id[:10]}... not connected")
                    await websocket.send_json({
                        "type": "error",
                        "error": "target_offline",
                        "message": "Target user is not connected.",
                        "target": target_id
                    })
            
            # Handle other message types
            elif msg_type == "request_verification":
                if target_id:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "verification_requested",
                            "from": client_id
                        }),
                        poll_id,
                        target_id
                    )
            
            elif msg_type == "accept_verification":
                await manager.broadcast_to_poll(
                    json.dumps({
                        "type": "verification_accepted",
                        "verifier": client_id,
                        "verified": target_id
                    }),
                    poll_id
                )
            
            else:
                # Generic message relay
                if target_id:
                    target_ws = manager.active_connections.get(poll_id, {}).get(target_id)
                    if target_ws:
                        message["from"] = client_id
                        await target_ws.send_json(message)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "error": "target_offline",
                            "message": "Target user not available."
                        })
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
