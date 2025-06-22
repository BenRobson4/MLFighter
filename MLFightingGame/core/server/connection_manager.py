import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional
from ..shop import ShopManager
from ..globals.constants import ITEM_DIRECTORY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.shop_manager = ShopManager(starting_gold=1000, items_directory=ITEM_DIRECTORY)
        
        # Message handlers mapping
        self.message_handlers = {
            "purchase_option": self.handle_purchase_message,
            "request_options": self.handle_options_request,
            "refresh_shop": self.handle_refresh_request,
            "get_purchases": self.handle_purchases_request,
            "get_status": self.handle_status_request,
        }
        
    async def register_client(self, websocket, client_id: str):
        """Register a new client connection"""
        self.clients[client_id] = {
            "websocket": websocket,
            "connected": True
        }
        
        # Register with shop manager
        self.shop_manager.register_client(client_id)
        
        logger.info(f"Client {client_id} connected")
        
    async def unregister_client(self, client_id: str):
        """Remove a client connection"""
        if client_id in self.clients:
            self.clients[client_id]["connected"] = False
            logger.info(f"Client {client_id} disconnected")
            
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
            
    async def handle_purchase_message(self, client_id: str, data: Dict[str, Any]):
        """Handle purchase request"""
        item_id = data.get("option_id")
        
        if not item_id:
            await self.send_message(client_id, {
                "type": "error",
                "message": "No item ID provided"
            })
            return
            
        # Process purchase through shop manager
        success, reason, purchase = self.shop_manager.process_purchase(client_id, item_id)
        
        # Send result
        await self.send_message(client_id, {
            "type": "purchase_result",
            "success": success,
            "option_id": item_id,
            "remaining_gold": self.shop_manager.get_client_gold(client_id),
            "reason": reason
        })
        
        # Send updated options if successful
        if success:
            await self.handle_options_request(client_id, {})
            
    async def handle_refresh_request(self, client_id: str, data: Dict[str, Any]):
        """Handle shop refresh request"""
        success, message = self.shop_manager.refresh_shop(client_id)
        
        if success:
            # Send new shop items
            await self.handle_options_request(client_id, {})
            
        # Send refresh result
        await self.send_message(client_id, {
            "type": "refresh_result",
            "success": success,
            "message": message,
            "remaining_gold": self.shop_manager.get_client_gold(client_id)
        })
        
    async def handle_options_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for available options"""
        shop_items = self.shop_manager.get_current_shop_items(client_id)
        
        await self.send_message(client_id, {
            "type": "options",
            "data": shop_items,
            "client_gold": self.shop_manager.get_client_gold(client_id),
            "refresh_cost": ShopManager.REFRESH_COST
        })
        
    async def handle_purchases_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for purchase history"""
        summary = self.shop_manager.get_purchase_summary(client_id)
        
        await self.send_message(client_id, {
            "type": "purchases_list",
            "purchases": summary["purchase_history"],
            "total_spent": summary["total_spent"],
            "items_owned": summary["items_owned"]
        })
        
    async def handle_status_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for client status"""
        summary = self.shop_manager.get_purchase_summary(client_id)
        
        await self.send_message(client_id, {
            "type": "status",
            "gold": summary["remaining_gold"],
            "items_owned": summary["items_owned"],
            "total_purchases": summary["total_purchases"]
        })
            
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """Route messages to appropriate handlers"""
        msg_type = message.get("type")
        
        if msg_type in self.message_handlers:
            handler = self.message_handlers[msg_type]
            await handler(client_id, message)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })
            
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
                
                # Send welcome message
                await self.send_message(client_id, {
                    "type": "connected",
                    "client_id": client_id,
                    "starting_gold": self.shop_manager.get_client_gold(client_id)
                })
                
                # Send initial options
                await asyncio.sleep(0.5)
                await self.handle_options_request(client_id, {})
                
                # Handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_client_message(client_id, data)
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
            await asyncio.Future()  # Run forever§