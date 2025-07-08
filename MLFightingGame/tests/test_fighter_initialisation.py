
# Import your server components
from ..core.shop.shop_manager import ShopManager
from ..core.shop.fighter_option_generator import FighterOptionGenerator
from ..core.server.session.client_session import ClientSession
from ..core.server.protocols.message_types import GamePhase
from ..core.players import Player
from ..core.server.coordinators.game_coordinator import GameCoordinator
from ..core.server.protocols.message_types import ClientMessageType, ServerMessageType
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import asyncio
import threading
from typing import Dict, Any, Optional, List
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import asyncio
import threading
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

class FighterSelectionTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Fighter Selection & Shop System Tester - Client Simulator")
        self.root.geometry("1200x800")
        
        # Initialize mock server components
        self.shop_manager = ShopManager(starting_gold=1000)
        self.client_id = "test_client_001"
        self.session = ClientSession(client_id=self.client_id)
        self.current_fighter_options = {}
        
        # Client state (what a real client would track)
        self.client_state = {
            "connected": False,
            "gold": 0,
            "current_shop": [],
            "fighter_options": [],
            "phase": None
        }
        
        # Create UI
        self.setup_ui()
        
        # Log initial state
        self.log("Client simulator initialized", "info")
        
    def setup_ui(self):
        """Create the UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel - Client Controls
        control_frame = ttk.LabelFrame(main_frame, text="Client Actions", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Connection section
        conn_frame = ttk.LabelFrame(control_frame, text="1. Connection", padding="5")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(conn_frame, text="Connect to Server", 
                  command=self.send_connect).pack(fill=tk.X)
        
        # Fighter selection section
        fighter_frame = ttk.LabelFrame(control_frame, text="2. Fighter Selection", padding="5")
        fighter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(fighter_frame, text="Request Fighter Options", 
                  command=self.send_request_fighter_options).pack(fill=tk.X, pady=(0, 5))
        
        self.fighter_selection_frame = ttk.Frame(fighter_frame)
        self.fighter_selection_frame.pack(fill=tk.X)
        
        # Shop section
        shop_frame = ttk.LabelFrame(control_frame, text="3. Shop Actions", padding="5")
        shop_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(shop_frame, text="Request Shop Items", 
                  command=self.send_request_shop).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(shop_frame, text="Refresh Shop (10g)", 
                  command=self.send_refresh_shop).pack(fill=tk.X, pady=(0, 5))
        
        self.shop_items_frame = ttk.Frame(shop_frame)
        self.shop_items_frame.pack(fill=tk.X)
        
        # Game flow section
        flow_frame = ttk.LabelFrame(control_frame, text="4. Game Flow", padding="5")
        flow_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(flow_frame, text="Send Shop Complete", 
                  command=self.send_shop_complete).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(flow_frame, text="Send Replay Viewed", 
                  command=self.send_replay_viewed).pack(fill=tk.X)
        
        # Client status section
        status_frame = ttk.LabelFrame(control_frame, text="Client Status", padding="5")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Not connected")
        self.status_label.pack()
        
        self.gold_label = ttk.Label(status_frame, text="Gold: -")
        self.gold_label.pack()
        
        self.phase_label = ttk.Label(status_frame, text="Phase: -")
        self.phase_label.pack()
        
        # Middle panel - Message log
        message_frame = ttk.LabelFrame(main_frame, text="Client-Server Messages", padding="10")
        message_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.message_log = scrolledtext.ScrolledText(message_frame, width=40, height=30)
        self.message_log.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Server state (for debugging)
        state_frame = ttk.LabelFrame(main_frame, text="Server State (Debug)", padding="10")
        state_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.state_text = scrolledtext.ScrolledText(state_frame, width=40, height=30)
        self.state_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    # ==================== CLIENT MESSAGE SENDERS ====================
    
    def send_connect(self):
        """Send CONNECT message"""
        message = {
            "type": ClientMessageType.CONNECT.value,
            "client_id": self.client_id,
            "timestamp": datetime.now().isoformat()
        }
        self.send_message(message)
    
    def send_request_fighter_options(self):
        """Request fighter options (client doesn't have specific message for this)"""
        # In real implementation, this might be automatic after connection
        # For now, simulate with a generic request
        message = {
            "type": "request_fighter_options",
            "client_id": self.client_id
        }
        self.send_message(message)
    
    def send_select_fighter(self, option_id: str):
        """Send fighter selection"""
        message = {
            "type": "select_fighter",
            "client_id": self.client_id,
            "option_id": option_id
        }
        self.send_message(message)
    
    def send_request_shop(self):
        """Request current shop items"""
        message = {
            "type": ClientMessageType.REQUEST_OPTIONS.value,
            "client_id": self.client_id
        }
        self.send_message(message)
    
    def send_purchase_item(self, item_id: str):
        """Send purchase request"""
        message = {
            "type": ClientMessageType.PURCHASE_OPTION.value,
            "client_id": self.client_id,
            "option_id": item_id
        }
        self.send_message(message)
    
    def send_refresh_shop(self):
        """Send shop refresh request"""
        message = {
            "type": ClientMessageType.REFRESH_SHOP.value,
            "client_id": self.client_id
        }
        self.send_message(message)
    
    def send_shop_complete(self):
        """Send shop phase complete"""
        if self.client_state["phase"] == GamePhase.INITIAL_SHOP.value:
            message_type = ClientMessageType.INITIAL_SHOP_COMPLETE.value
        else:
            message_type = ClientMessageType.SHOP_PHASE_COMPLETE.value
            
        message = {
            "type": message_type,
            "client_id": self.client_id,
            "purchases": []  # Could track actual purchases if needed
        }
        self.send_message(message)
    
    def send_replay_viewed(self):
        """Send replay viewed confirmation"""
        message = {
            "type": ClientMessageType.REPLAY_VIEWED.value,
            "client_id": self.client_id
        }
        self.send_message(message)
    
    # ==================== MESSAGE HANDLING ====================
    
    def send_message(self, message: Dict[str, Any]):
        """Send a message and process server response"""
        self.log(f"CLIENT → SERVER: {message['type']}", "send")
        self.log(json.dumps(message, indent=2), "send")
        
        # Simulate server processing the message
        response = self.mock_server_handle_message(message)
        
        if response:
            self.log(f"SERVER → CLIENT: {response['type']}", "receive")
            self.log(json.dumps(response, indent=2), "receive")
            self.handle_server_response(response)
    
    def mock_server_handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock server message handler"""
        msg_type = message.get("type")
        
        if msg_type == ClientMessageType.CONNECT.value:
            # Register client
            self.shop_manager.register_client(self.client_id)
            self.session.current_phase = GamePhase.INITIAL_SHOP
            
            return {
                "type": ServerMessageType.CONNECTED.value,
                "client_id": self.client_id,
                "starting_gold": self.shop_manager.get_client_gold(self.client_id),
                "phase": GamePhase.INITIAL_SHOP.value
            }
            
        elif msg_type == "request_fighter_options":
            # Generate fighter options
            fighter_options = self.shop_manager.generate_fighter_options(self.client_id)
            self.current_fighter_options = {opt['option_id']: opt for opt in fighter_options}
            
            return {
                "type": ServerMessageType.INITIAL_SHOP_READY.value,
                "phase": "fighter_selection",
                "fighter_options": fighter_options,
                "message": "Choose your fighter and learning style"
            }
            
        elif msg_type == "select_fighter":
            option_id = message.get("option_id")
            success, msg, player_config = self.shop_manager.process_fighter_selection(
                self.client_id, option_id
            )
            
            if success:
                # Create player on server
                option = self.current_fighter_options[option_id]
                self.session.player = Player(
                    player_id=1,
                    fighter_name=player_config['fighter_name'],
                    starting_gold=player_config['starting_gold'],
                    starting_level=player_config['starting_level'],
                    learning_parameters=player_config['learning_parameters'],
                    num_actions=6,
                    num_features=20,
                    initial_feature_mask=np.array(option['initial_feature_mask'])
                )
                
                # Send shop items
                shop_items = self.shop_manager.get_current_shop_items(self.client_id)
                
                return {
                    "type": ServerMessageType.OPTIONS.value,
                    "phase": "initial_items",
                    "data": shop_items,
                    "client_gold": self.shop_manager.get_client_gold(self.client_id),
                    "message": "Fighter selected! Choose your starting items"
                }
                
        elif msg_type == ClientMessageType.REQUEST_OPTIONS.value:
            shop_items = self.shop_manager.get_current_shop_items(self.client_id)
            
            return {
                "type": ServerMessageType.OPTIONS.value,
                "data": shop_items,
                "client_gold": self.shop_manager.get_client_gold(self.client_id),
                "refresh_cost": ShopManager.REFRESH_COST
            }
            
        elif msg_type == ClientMessageType.PURCHASE_OPTION.value:
            item_id = message.get("option_id")
            success, reason, purchase = self.shop_manager.process_purchase(self.client_id, item_id)
            
            # Apply to player if successful
            if success and self.session.player and item_id in self.shop_manager.all_items:
                item = self.shop_manager.all_items[item_id]
                item_data = {
                    "category": item.category,
                    "subcategory": item.subcategory,
                    "name": item.name,
                    "description": item.description,
                    "properties": item.properties or {}
                }
                if item.properties:
                    for key, value in item.properties.items():
                        if key not in item_data:
                            item_data[key] = value
                self.session.player.add_item(item_id, item_data)
            
            return {
                "type": ServerMessageType.PURCHASE_RESULT.value,
                "success": success,
                "option_id": item_id,
                "remaining_gold": self.shop_manager.get_client_gold(self.client_id),
                "reason": reason
            }
            
        elif msg_type == ClientMessageType.REFRESH_SHOP.value:
            success, message_text = self.shop_manager.refresh_shop(self.client_id)
            
            response = {
                "type": ServerMessageType.REFRESH_RESULT.value,
                "success": success,
                "message": message_text,
                "remaining_gold": self.shop_manager.get_client_gold(self.client_id)
            }
            
            if success:
                # Also send new shop items
                shop_items = self.shop_manager.get_current_shop_items(self.client_id)
                response["shop_items"] = shop_items
                
            return response
            
        elif msg_type == ClientMessageType.INITIAL_SHOP_COMPLETE.value:
            self.session.initial_shop_complete = True
            self.session.current_phase = GamePhase.FIGHTING
            
            # Simulate fight and send replay
            return {
                "type": ServerMessageType.GAME_STATE_CHANGE.value,
                "phase": GamePhase.FIGHTING.value,
                "message": "Starting fight..."
            }
            
        elif msg_type == ClientMessageType.SHOP_PHASE_COMPLETE.value:
            self.session.current_phase = GamePhase.FIGHTING
            self.session.fights_completed += 1
            
            return {
                "type": ServerMessageType.GAME_STATE_CHANGE.value,
                "phase": GamePhase.FIGHTING.value,
                "message": "Starting next fight..."
            }
            
        elif msg_type == ClientMessageType.REPLAY_VIEWED.value:
            # Award gold and return to shop
            gold_earned = 100
            self.shop_manager.add_gold_to_client(self.client_id, gold_earned)
            self.shop_manager.regenerate_shop(self.client_id)
            self.session.current_phase = GamePhase.SHOP_PHASE
            
            shop_items = self.shop_manager.get_current_shop_items(self.client_id)
            
            return {
                "type": ServerMessageType.SHOP_PHASE_START.value,
                "data": shop_items,
                "client_gold": self.shop_manager.get_client_gold(self.client_id),
                "refresh_cost": ShopManager.REFRESH_COST,
                "gold_earned": gold_earned,
                "message": f"Fight complete! Earned {gold_earned} gold"
            }
            
        return None
    
    def handle_server_response(self, response: Dict[str, Any]):
        """Handle server response and update UI"""
        msg_type = response.get("type")
        
        if msg_type == ServerMessageType.CONNECTED.value:
            self.client_state["connected"] = True
            self.client_state["gold"] = response.get("starting_gold", 0)
            self.client_state["phase"] = response.get("phase")
            self.status_label.config(text=f"Connected as {response['client_id']}")
            
        elif msg_type == ServerMessageType.INITIAL_SHOP_READY.value:
            # Display fighter options
            fighter_options = response.get("fighter_options", [])
            self.client_state["fighter_options"] = fighter_options
            
            for widget in self.fighter_selection_frame.winfo_children():
                widget.destroy()
                
            for option in fighter_options:
                frame = ttk.Frame(self.fighter_selection_frame)
                frame.pack(fill=tk.X, pady=2)
                
                info = f"{option['fighter_name']} - {option['active_features']} features"
                ttk.Label(frame, text=info, width=30).pack(side=tk.LEFT)
                
                ttk.Button(frame, text="Select", 
                          command=lambda opt_id=option['option_id']: self.send_select_fighter(opt_id)
                ).pack(side=tk.RIGHT)
                
        elif msg_type == ServerMessageType.OPTIONS.value:
            # Display shop items
            shop_items = response.get("data", [])
            self.client_state["current_shop"] = shop_items
            self.client_state["gold"] = response.get("client_gold", 0)
            
            for widget in self.shop_items_frame.winfo_children():
                widget.destroy()
                
            for item in shop_items:
                frame = ttk.Frame(self.shop_items_frame)
                frame.pack(fill=tk.X, pady=2)
                
                info = f"{item['name']} - {item['cost']}g"
                if not item['can_afford']:
                    info += " (Can't afford)"
                
                label = ttk.Label(frame, text=info, width=30)
                label.pack(side=tk.LEFT)
                
                btn = ttk.Button(frame, text="Buy", 
                               command=lambda item_id=item['id']: self.send_purchase_item(item_id))
                btn.pack(side=tk.RIGHT)
                
                if not item['can_afford'] or item.get('already_purchased', False):
                    btn.config(state='disabled')
                    
        elif msg_type == ServerMessageType.PURCHASE_RESULT.value:
            if response.get("success"):
                self.client_state["gold"] = response.get("remaining_gold", 0)
                # Request updated shop
                self.send_request_shop()
                
        elif msg_type == ServerMessageType.REFRESH_RESULT.value:
            if response.get("success"):
                self.client_state["gold"] = response.get("remaining_gold", 0)
                if "shop_items" in response:
                    # Update shop display
                    self.handle_server_response({
                        "type": ServerMessageType.OPTIONS.value,
                        "data": response["shop_items"],
                        "client_gold": self.client_state["gold"]
                    })
                    
        elif msg_type == ServerMessageType.GAME_STATE_CHANGE.value:
            self.client_state["phase"] = response.get("phase")
            
        elif msg_type == ServerMessageType.SHOP_PHASE_START.value:
            self.client_state["phase"] = GamePhase.SHOP_PHASE.value
            self.client_state["gold"] = response.get("client_gold", 0)
            # Display new shop
            self.handle_server_response({
                "type": ServerMessageType.OPTIONS.value,
                "data": response.get("data", []),
                "client_gold": self.client_state["gold"]
            })
        
        # Update displays
        self.update_client_display()
        self.update_server_state_display()
    
    def log(self, message: str, msg_type: str = "info"):
        """Log a message to the message log"""
        # Color coding
        self.message_log.tag_config("info", foreground="black")
        self.message_log.tag_config("send", foreground="blue")
        self.message_log.tag_config("receive", foreground="green")
        self.message_log.tag_config("error", foreground="red")
        
        self.message_log.insert(tk.END, f"{message}\n", msg_type)
        self.message_log.see(tk.END)
    
    def update_client_display(self):
        """Update client status display"""
        self.gold_label.config(text=f"Gold: {self.client_state['gold']}")
        self.phase_label.config(text=f"Phase: {self.client_state['phase']}")
    
    def update_server_state_display(self):
        """Update the server state display panel"""
        state_info = {
            "server_session": {
                "client_id": self.client_id,
                "current_phase": self.session.current_phase.value if self.session.current_phase else "None",
                "initial_shop_complete": self.session.initial_shop_complete,
                "fights_completed": self.session.fights_completed,
            },
            "shop_manager": {
                "client_gold": self.shop_manager.get_client_gold(self.client_id),
                "items_in_current_shop": len(self.shop_manager.client_current_shop.get(self.client_id, [])),
                "total_purchases": len(self.shop_manager.client_purchases.get(self.client_id, [])),
            }
        }
        
        if self.session.player:
            state_info["player"] = {
                "fighter_name": self.session.player.fighter.name,
                "level": self.session.player.level,
                "active_features": int(sum(self.session.player.feature_mask.cpu().numpy())),
                "total_features": self.session.player.num_features,
                "epsilon": f"{self.session.player.learning_parameters.epsilon:.3f}",
            }
            
            state_info["inventory"] = {
                "weapons": self.session.player.inventory.get_weapon_count(),
                "armour": self.session.player.inventory.get_armour_count(),
                "features": list(self.session.player.inventory.features),
                "equipped_weapon": self.session.player.inventory.get_equipped_weapon().name if self.session.player.inventory.get_equipped_weapon() else "None",
                "equipped_armour": self.session.player.inventory.get_equipped_armour().name if self.session.player.inventory.get_equipped_armour() else "None",
            }
        
        self.state_text.delete(1.0, tk.END)
        self.state_text.insert(1.0, json.dumps(state_info, indent=2))

def main():
    root = tk.Tk()
    app = FighterSelectionTester(root)
    root.mainloop()

if __name__ == "__main__":
    main()