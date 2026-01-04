"""
WebSocket routes for live log streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.services.raw_log_broadcaster import raw_log_broadcaster
import json

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/logs/live")
async def websocket_live_logs(websocket: WebSocket):
    """
    WebSocket endpoint for live raw log streaming.
    
    Clients can subscribe to specific log sources:
    - Send: {"type": "subscribe", "log_source": "auth"} 
    - Send: {"type": "subscribe", "log_source": "all"} for all sources
    
    Supported log sources: "auth", "ufw", "kern", "syslog", "messages", "all"
    """
    connection_id = None
    try:
        print(f"✓ WebSocket connection attempt from {websocket.client}")
        await websocket.accept()
        print(f"✓ WebSocket connection accepted")
        
        # Add connection to broadcaster
        connection_id = raw_log_broadcaster.add_connection(websocket)
        print(f"✓ Connection {connection_id} added to broadcaster")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to live log stream",
            "connection_id": connection_id
        })
        print(f"✓ Connection confirmation sent to {connection_id}")
        
        # Listen for messages from client
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")
                    log_source = message.get("log_source")
                    
                    if msg_type == "subscribe":
                        if log_source in ["auth", "ufw", "kern", "syslog", "messages", "all"]:
                            raw_log_broadcaster.subscribe(connection_id, log_source)
                            await websocket.send_json({
                                "type": "subscribed",
                                "log_source": log_source,
                                "message": f"Subscribed to {log_source} logs"
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Invalid log source: {log_source}. Valid sources: auth, ufw, kern, syslog, messages, all"
                            })
                    
                    elif msg_type == "unsubscribe":
                        if log_source:
                            raw_log_broadcaster.unsubscribe(connection_id, log_source)
                            await websocket.send_json({
                                "type": "unsubscribed",
                                "log_source": log_source,
                                "message": f"Unsubscribed from {log_source} logs"
                            })
                    
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown message type: {msg_type}"
                        })
                
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
            
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                print(f"✗ Error in WebSocket handler: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        print(f"✓ Client disconnected: {connection_id}")
    
    except Exception as e:
        import traceback
        print(f"✗ WebSocket error: {e}")
        print(f"✗ Traceback: {traceback.format_exc()}")
    
    finally:
        # Remove connection from broadcaster
        if connection_id:
            try:
                raw_log_broadcaster.remove_connection(connection_id)
            except Exception as e:
                print(f"✗ Error removing connection {connection_id}: {e}")

