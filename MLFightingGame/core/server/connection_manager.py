import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .coordinators.game_coordinator import GameCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing ONLY - no game logic"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.game_coordinator: GameCoordinator = None  # Will be injected
        
    def set_game_coordinator(self, coordinator):
        """Inject the game coordinator for message handling"""
        self.game_coordinator = coordinator
        
    async def register_client(self, websocket, client_id: str):
        """Register a new client connection"""
        self.clients[client_id] = {
            "websocket": websocket,
            "connected": True
        }
        logger.info(f"Client {client_id} connected")
        
        # Notify game coordinator of new connection
        if self.game_coordinator:
            await self.game_coordinator.on_client_connected(client_id, websocket)
        
    async def unregister_client(self, client_id: str):
        """Remove a client connection"""
        if client_id in self.clients:
            self.clients[client_id]["connected"] = False
            logger.info(f"Client {client_id} disconnected")
            
            # Notify game coordinator of disconnection
            if self.game_coordinator:
                await self.game_coordinator.on_client_disconnected(client_id)
            
    async def send_message(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific client"""
        if client_id not in self.clients or not self.clients[client_id]["connected"]:
            logger.warning(f"Client {client_id} not connected")
            return False
            
        try:
            websocket = self.clients[client_id]["websocket"]
            await websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            return False
            
    async def handle_connection(self, websocket, path=None):
        """Handle a WebSocket connection"""
        client_id = None
        try:
            # Wait for client identification
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get("type") == "connect":
                client_id = data.get("client_id", str(id(websocket)))
                await self.register_client(websocket, client_id)
                
                # All game logic is handled by coordinator now
                # Just route messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if self.game_coordinator:
                            await self.game_coordinator.handle_client_message(client_id, data)
                        else:
                            logger.error("No game coordinator available")
                            await self.send_message(client_id, {
                                "type": "error",
                                "message": "Server not properly initialized"
                            })
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client {client_id}")
                        await self.send_message(client_id, {
                            "type": "error",
                            "message": "Invalid JSON format"
                        })
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} connection closed")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id:
                await self.unregister_client(client_id)
                
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()  # Run forever