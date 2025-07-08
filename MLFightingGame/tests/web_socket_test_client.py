import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import websockets
import json
import threading
from datetime import datetime
import uuid

class WebSocketTestClient:
    def __init__(self, root):
        self.root = root
        self.root.title("WebSocket Test Client")
        self.root.geometry("1200x800")
        
        # WebSocket connection
        self.websocket = None
        self.client_id = f"test_client_{uuid.uuid4().hex[:8]}"
        self.connected = False
        
        # Async event loop in separate thread
        self.loop = None
        self.thread = None
        
        # Current game state tracking
        self.current_phase = "CONNECTING"
        self.current_replay_index = 0
        self.total_replays = 0
        self.current_gold = 0
        self.current_options = []  # Store current shop/fighter options
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ==================== CONNECTION SECTION ====================
        connection_frame = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Server info
        ttk.Label(connection_frame, text="Server:").grid(row=0, column=0, sticky=tk.W)
        self.server_entry = ttk.Entry(connection_frame, width=20)
        self.server_entry.insert(0, "localhost")
        self.server_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W)
        self.port_entry = ttk.Entry(connection_frame, width=10)
        self.port_entry.insert(0, "8765")
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # Connection buttons
        self.connect_btn = ttk.Button(connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=0, column=4, padx=5)
        
        self.disconnect_btn = ttk.Button(connection_frame, text="Disconnect", command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=5, padx=5)
        
        # Status label
        self.status_label = ttk.Label(connection_frame, text=f"Status: Disconnected | Client ID: {self.client_id}")
        self.status_label.grid(row=1, column=0, columnspan=6, pady=5)
        
        # Gold display
        self.gold_label = ttk.Label(connection_frame, text="Gold: 0")
        self.gold_label.grid(row=2, column=0, columnspan=6, pady=5)
        
        # ==================== CURRENT OPTIONS SECTION ====================
        options_frame = ttk.LabelFrame(main_frame, text="Current Options (Fighter/Shop)", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Options display
        self.options_text = scrolledtext.ScrolledText(options_frame, height=10, width=50, wrap=tk.WORD)
        self.options_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Option selection
        ttk.Label(options_frame, text="Select Option ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.option_id_entry = ttk.Entry(options_frame, width=30)
        self.option_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(options_frame, text="Purchase Selected", 
                  command=self.purchase_selected_option).grid(row=1, column=2, padx=5, pady=5)
        
        # Quick select buttons (will be populated dynamically)
        self.quick_select_frame = ttk.Frame(options_frame)
        self.quick_select_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        # ==================== GAME FLOW SECTION ====================
        game_frame = ttk.LabelFrame(main_frame, text="Game Flow Messages", padding="10")
        game_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        # Phase info
        self.phase_label = ttk.Label(game_frame, text="Current Phase: CONNECTING")
        self.phase_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Initial Shop
        ttk.Label(game_frame, text="Initial Shop:").grid(row=1, column=0, sticky=tk.W)
        ttk.Button(game_frame, text="Complete Initial Shop", 
                  command=lambda: self.send_message({
                      "type": "initial_shop_complete"
                  })).grid(row=1, column=1, padx=5)
        
        # Replay Phase
        ttk.Label(game_frame, text="Replay Phase:").grid(row=2, column=0, sticky=tk.W)
        ttk.Button(game_frame, text="Replay Viewed", 
                  command=lambda: self.send_message({
                      "type": "replay_viewed"
                  })).grid(row=2, column=1, padx=5)
        
        # Shop Phase
        ttk.Label(game_frame, text="Shop Phase:").grid(row=3, column=0, sticky=tk.W)
        ttk.Button(game_frame, text="Complete Shop Phase", 
                  command=lambda: self.send_message({
                      "type": "shop_phase_complete"
                  })).grid(row=3, column=1, padx=5)
        
        # ==================== REPLAY NAVIGATION SECTION ====================
        replay_frame = ttk.LabelFrame(main_frame, text="Replay Navigation", padding="10")
        replay_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Navigation buttons
        ttk.Button(replay_frame, text="← Previous", 
                  command=lambda: self.send_message({
                      "type": "request_previous_replay",
                      "current_index": self.current_replay_index
                  })).grid(row=0, column=0, padx=5)
        
        ttk.Button(replay_frame, text="Next →", 
                  command=lambda: self.send_message({
                      "type": "request_next_replay",
                      "current_index": self.current_replay_index
                  })).grid(row=0, column=1, padx=5)
        
        ttk.Button(replay_frame, text="List All", 
                  command=lambda: self.send_message({
                      "type": "request_replay_list"
                  })).grid(row=0, column=2, padx=5)
        
        # Current replay info
        self.replay_info_label = ttk.Label(replay_frame, text="Replay: 0/0")
        self.replay_info_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # ==================== SHOP ACTIONS SECTION ====================
        shop_frame = ttk.LabelFrame(main_frame, text="Shop Actions", padding="10")
        shop_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Shop actions
        ttk.Button(shop_frame, text="Request Options", 
                  command=lambda: self.send_message({
                      "type": "request_options"
                  })).grid(row=0, column=0, padx=5)
        
        ttk.Button(shop_frame, text="Refresh Shop (-10 gold)", 
                  command=lambda: self.send_message({
                      "type": "refresh_shop"
                  })).grid(row=0, column=1, padx=5)
        
        ttk.Button(shop_frame, text="Get Purchases", 
                  command=lambda: self.send_message({
                      "type": "get_purchases"
                  })).grid(row=0, column=2, padx=5)
        
        ttk.Button(shop_frame, text="Get Status", 
                  command=lambda: self.send_message({
                      "type": "get_status"
                  })).grid(row=0, column=3, padx=5)
        
        # ==================== MESSAGE LOG SECTION ====================
        log_frame = ttk.LabelFrame(main_frame, text="Message Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Message log with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=100, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure tags for colored text
        self.log_text.tag_config("sent", foreground="blue")
        self.log_text.tag_config("received", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("info", foreground="gray")
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", 
                  command=lambda: self.log_text.delete(1.0, tk.END)).grid(row=1, column=0, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        options_frame.columnconfigure(0, weight=1)
        options_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message, tag="info"):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        
    def update_options_display(self, options_data, phase="shop"):
        """Update the options display with current fighter or shop options"""
        self.options_text.delete(1.0, tk.END)
        self.current_options = options_data
        
        # Clear quick select buttons
        for widget in self.quick_select_frame.winfo_children():
            widget.destroy()
        
        if phase == "fighter_selection":
            self.options_text.insert(tk.END, "=== FIGHTER SELECTION ===\n\n")
            for i, option in enumerate(options_data):
                self.options_text.insert(tk.END, f"Option {i+1}: {option.get('fighter_name', 'Unknown')}\n")
                self.options_text.insert(tk.END, f"  ID: {option.get('option_id', 'N/A')}\n")
                self.options_text.insert(tk.END, f"  Style: {option.get('learning_style', 'N/A')}\n")
                self.options_text.insert(tk.END, f"  Description: {option.get('description', 'N/A')}\n")
                self.options_text.insert(tk.END, "\n")
                
                # Create quick select button
                btn = ttk.Button(self.quick_select_frame, 
                               text=f"{option.get('fighter_name', 'Option ' + str(i+1))}", 
                               command=lambda opt_id=option.get('option_id'): self.quick_select_option(opt_id))
                btn.grid(row=0, column=i, padx=2)
                
        else:  # Shop items
            self.options_text.insert(tk.END, "=== SHOP ITEMS ===\n\n")
            for i, item in enumerate(options_data):
                self.options_text.insert(tk.END, f"{i+1}. {item.get('name', 'Unknown')}\n")
                self.options_text.insert(tk.END, f"  ID: {item.get('id', 'N/A')}\n")
                self.options_text.insert(tk.END, f"  Cost: {item.get('cost', 0)} gold\n")
                self.options_text.insert(tk.END, f"  Category: {item.get('category', 'N/A')}\n")
                self.options_text.insert(tk.END, f"  Description: {item.get('description', 'N/A')}\n")
                if item.get('already_purchased'):
                    self.options_text.insert(tk.END, "  [ALREADY PURCHASED]\n")
                if not item.get('can_afford'):
                    self.options_text.insert(tk.END, "  [CANNOT AFFORD]\n")
                self.options_text.insert(tk.END, "\n")
                
                # Create quick select button
                btn = ttk.Button(self.quick_select_frame, 
                               text=f"{item.get('name', 'Item ' + str(i+1))[:15]}... ({item.get('cost', 0)}g)", 
                               command=lambda item_id=item.get('id'): self.quick_select_option(item_id))
                if not item.get('can_afford') or item.get('already_purchased'):
                    btn.config(state=tk.DISABLED)
                btn.grid(row=i // 3, column=i % 3, padx=2, pady=2)
                
    def quick_select_option(self, option_id):
        """Quick select an option"""
        self.option_id_entry.delete(0, tk.END)
        self.option_id_entry.insert(0, option_id)
        self.purchase_selected_option()
        
    def purchase_selected_option(self):
        """Purchase the selected option"""
        option_id = self.option_id_entry.get()
        if not option_id:
            self.log_message("No option ID entered!", "error")
            return
            
        self.send_message({
            "type": "purchase_option",
            "option_id": option_id
        })
        
    def connect_to_server(self):
        """Connect to the WebSocket server"""
        if self.connected:
            return
            
        server = self.server_entry.get()
        port = self.port_entry.get()
        
        # Start async event loop in separate thread
        self.thread = threading.Thread(target=self._run_async_loop, args=(server, port))
        self.thread.daemon = True
        self.thread.start()
        
    def _run_async_loop(self, server, port):
        """Run the async event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._connect_websocket(server, port))
        except Exception as e:
            self.root.after(0, self.log_message, f"Connection error: {e}", "error")
            self.root.after(0, self._update_connection_status, False)
            
    async def _connect_websocket(self, server, port):
        """Establish WebSocket connection and handle messages"""
        uri = f"ws://{server}:{port}"
        self.log_message(f"Connecting to {uri}...", "info")
        
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connected = True
                self.root.after(0, self._update_connection_status, True)
                self.root.after(0, self.log_message, f"Connected to {uri}", "info")
                
                # Send initial connect message
                connect_msg = {
                    "type": "connect",
                    "client_id": self.client_id
                }
                await websocket.send(json.dumps(connect_msg))
                self.root.after(0, self.log_message, f"SENT: {json.dumps(connect_msg, indent=2)}", "sent")
                
                # Listen for messages
                async for message in websocket:
                    data = json.loads(message)
                    self.root.after(0, self._handle_server_message, data)
                    
        except websockets.exceptions.ConnectionClosed:
            self.root.after(0, self.log_message, "Connection closed by server", "error")
        except Exception as e:
            self.root.after(0, self.log_message, f"WebSocket error: {e}", "error")
        finally:
            self.connected = False
            self.websocket = None
            self.root.after(0, self._update_connection_status, False)
            
    def _handle_server_message(self, data):
        """Handle messages received from server"""
        self.log_message(f"RECEIVED: {json.dumps(data, indent=2)}", "received")
        
        msg_type = data.get("type")
        
        # Update UI based on message type
        if msg_type == "connected":
            self.status_label.config(text=f"Status: Connected | Client ID: {data.get('client_id', self.client_id)}")
            self.current_gold = data.get('starting_gold', 0)
            self.gold_label.config(text=f"Gold: {self.current_gold}")

        elif msg_type == "matchmaking_started":
            self.current_phase = "MATCHMAKING"
            self.phase_label.config(text=f"Current Phase: {self.current_phase}")
            queue_pos = data.get('queue_position', 0)
            self.log_message(f"Entered matchmaking queue. Position: {queue_pos}", "info")
            
        elif msg_type == "match_found":
            opponent = data.get('opponent', {})
            match_id = data.get('match_id', 'unknown')
            self.log_message(f"Match found! Opponent: {opponent.get('name', 'Unknown')} Match ID: {match_id}", "info")

        elif msg_type == "waiting_for_opponent":
            self.log_message(data.get('message', 'Waiting for opponent...'), "info")
            
        elif msg_type == "opponent_ready":
            self.log_message(data.get('message', 'Opponent is ready!'), "info")

        elif msg_type == "opponent_disconnected":
            self.log_message("Opponent disconnected!", "error")
            
        elif msg_type == "initial_shop_ready":
            self.current_phase = "INITIAL_SHOP"
            self.phase_label.config(text=f"Current Phase: {self.current_phase}")
            fighter_options = data.get('fighter_options', [])
            self.update_options_display(fighter_options, "fighter_selection")
            
        elif msg_type == "options":
            phase = data.get('phase', 'shop')
            options_data = data.get('data', [])
            self.current_gold = data.get('client_gold', self.current_gold)
            self.gold_label.config(text=f"Gold: {self.current_gold}")
            self.update_options_display(options_data, phase)
            
        elif msg_type == "purchase_result":
            if data.get('success'):
                self.log_message(f"Purchase successful! Remaining gold: {data.get('remaining_gold', 0)}", "info")
                self.current_gold = data.get('remaining_gold', 0)
                self.gold_label.config(text=f"Gold: {self.current_gold}")
            else:
                self.log_message(f"Purchase failed: {data.get('reason', 'Unknown reason')}", "error")
                
        elif msg_type == "refresh_result":
            if data.get('success'):
                self.log_message(f"Shop refreshed! {data.get('message', '')}", "info")
                self.current_gold = data.get('remaining_gold', 0)
                self.gold_label.config(text=f"Gold: {self.current_gold}")
            else:
                self.log_message(f"Refresh failed: {data.get('message', 'Unknown reason')}", "error")
                
        elif msg_type == "fight_starting":
            self.current_phase = "FIGHTING"
            self.phase_label.config(text=f"Current Phase: {self.current_phase}")
            self.log_message(f"Fight starting! Opponent: {data.get('opponent', {}).get('name', 'Unknown')}", "info")
            
        elif msg_type == "batch_completed":
            wins = data.get("wins", 0)
            losses = data.get("losses", 0)
            win_rate = data.get("win_rate", 0)
            self.log_message(f"Batch completed! Wins: {wins}, Losses: {losses}, Win Rate: {win_rate:.1%}", "info")
            
        elif msg_type in ["replay_data", "replay_next", "replay_previous"]:
            self.current_phase = "VIEWING_REPLAY"
            self.phase_label.config(text=f"Current Phase: {self.current_phase}")
            self.current_replay_index = data.get("replay_index", 0)
            self.total_replays = data.get("total_replays", 0)
            self.replay_info_label.config(text=f"Replay: {self.current_replay_index + 1}/{self.total_replays}")
            
        elif msg_type == "shop_phase_start":
            self.current_phase = "SHOP_PHASE"
            self.phase_label.config(text=f"Current Phase: {self.current_phase}")
            shop_items = data.get('data', [])
            self.current_gold = data.get('client_gold', self.current_gold)
            self.gold_label.config(text=f"Gold: {self.current_gold}")
            self.update_options_display(shop_items, "shop")
            
        elif msg_type == "status":
            self.current_gold = data.get('gold', 0)
            self.gold_label.config(text=f"Gold: {self.current_gold}")
            self.log_message(f"Status - Gold: {self.current_gold}, Items: {len(data.get('items_owned', []))}", "info")
            
        elif msg_type == "error":
            self.log_message(f"ERROR: {data.get('message', 'Unknown error')}", "error")
            
    def send_message(self, message):
        """Send a message to the server"""
        if not self.connected or not self.websocket:
            self.log_message("Not connected to server!", "error")
            return
            
        # Send message asynchronously
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._send_message_async(message), self.loop)
            
    async def _send_message_async(self, message):
        """Async method to send message"""
        try:
            await self.websocket.send(json.dumps(message))
            self.root.after(0, self.log_message, f"SENT: {json.dumps(message, indent=2)}", "sent")
        except Exception as e:
            self.root.after(0, self.log_message, f"Send error: {e}", "error")
            
    def disconnect_from_server(self):
        """Disconnect from the server"""
        if self.websocket and self.connected:
            # Send disconnect message
            self.send_message({"type": "disconnect"})
            
            # Close connection
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
                
        self.connected = False
        self._update_connection_status(False)
        
    def _update_connection_status(self, connected):
        """Update UI based on connection status"""
        if connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"Status: Connected | Client ID: {self.client_id}")
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.status_label.config(text=f"Status: Disconnected | Client ID: {self.client_id}")
            
    def on_closing(self):
        """Handle window close event"""
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = WebSocketTestClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()