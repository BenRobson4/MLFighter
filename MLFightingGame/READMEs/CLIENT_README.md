# CLIENT_README.md

# Godot Client Architecture

This document describes the internal architecture and data flow of the Godot client for the auto-battling game.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Signal Flow](#signal-flow)
4. [Phase Lifecycle](#phase-lifecycle)
5. [Data Management](#data-management)
6. [Message Routing](#message-routing)

---

## Architecture Overview

### Scene Hierarchy

Main (Node)
├── GameController (Node)
│   └── NetworkManager (Node)
├── UI (CanvasLayer)
│   ├── ConnectionStatus (Control)
│   └── NotificationSystem (Control)
└── PhaseContainer (Node)
   └── [Current Phase Scene - Dynamically Loaded]

### AutoLoad Singletons (Global)
- **StaticDataManager** - Loads and manages static game data (items, fighters)
- **GameDataStore** - Stores session data (gold, inventory, stats)

---

## Core Components

### GameController
**Purpose:** Central orchestrator that manages phase transitions and message routing.

**Key Responsibilities:**
- Manages phase transitions via `transition_to_phase(phase_name: String)`
- Routes server messages to appropriate handlers
- Connects all component signals in `_ready()`
- Forwards messages to current phase via `_route_message_to_phase()`

### NetworkManager
**Purpose:** Handles WebSocket connection and message serialization.

**Key Functions:**
- `connect_to_server()` - Initiates WebSocket connection
- `send_message(message: Dictionary)` - Sends JSON to server
- `_process_incoming_messages()` - Polls and parses WebSocket data
- `_on_connection_established()` - Handles successful connection

**Emitted Signals:**
- `connected_to_server` - Connection established
- `disconnected_from_server` - Connection lost
- `connection_error(error: String)` - Connection error occurred
- `message_received(message: Dictionary)` - Server message received

### GameDataStore (Global Singleton)
**Purpose:** Persistent storage for all session data.

**Key Functions:**
- `set_fighter_data(fighter_id, fighter_name, level)` - Store selected fighter
- `set_gold(amount: int)` - Update gold amount
- `update_inventory(inventory: Dictionary)` - Update player inventory
- `update_stats(wins, losses, rounds)` - Update battle statistics
- `update_shop_items(items: Array)` - Store current shop offerings

**Emitted Signals:**
- `gold_changed(new_amount: int)` - Gold amount updated
- `fighter_selected(fighter_data: Dictionary)` - Fighter chosen
- `inventory_updated(inventory: Dictionary)` - Inventory changed
- `stats_updated(wins, losses, rounds)` - Battle stats changed

### StaticDataManager (Global Singleton)
**Purpose:** Manages static game data loaded from JSON files.

**Key Functions:**
- `get_item_data(item_id: String)` - Retrieve full item data
- `get_fighter_data(fighter_id: String)` - Retrieve full fighter data
- `validate_item_id(item_id: String)` - Check if item exists
- `validate_fighter_id(fighter_id: String)` - Check if fighter exists

**Emitted Signals:**
- `data_loaded(data_type: String)` - Specific data type loaded
- `all_data_loaded()` - All game data ready
- `data_load_failed(data_type, error)` - Data loading error

---

## Signal Flow

### Connection Flow

1. GameController._ready()
  → NetworkManager.connect_to_server()
  → WebSocket connects
  → NetworkManager.connected_to_server signal
  → GameController._on_connected_to_server()
  → Send initial connect message

2. Server responds with "connected" message
  → NetworkManager.message_received signal
  → GameController._on_message_received()
  → GameController._handle_connected_message()
  → GameDataStore.set_gold()

### Message Reception Flow

Server Message 
→ WebSocket 
→ NetworkManager._process_incoming_messages() 
→ NetworkManager.message_received signal
→ GameController._on_message_received()
→ Route to specific handler (e.g., _handle_shop_phase_start)
→ Update GameDataStore
→ GameDataStore emits relevant signals
→ UI components update

### Outgoing Message Flow

Phase calls GameController method (e.g., request_item_purchase)
→ GameController.send_message_to_server()
→ NetworkManager.send_message()
→ WebSocket sends JSON

---

## Phase Lifecycle

### Phase Transitions

1. **Loading New Phase:**
  - GameController.transition_to_phase(phase_name)
  - _cleanup_current_phase() - Disconnect signals, remove old phase
  - _load_phase_scene(phase_name) - Instantiate new phase from PHASE_SCENES
  - New phase added to PhaseContainer
  - Phase._ready() initializes UI and state

2. **Phase Communication:**
  - Phases call GameController methods for server communication
  - Phases listen to GameDataStore signals for data updates
  - Phases never communicate directly with NetworkManager

### Phase Flow

CONNECTION 
→ MATCHMAKING (automatic after connection)
→ FIGHTER_SELECTION (after match found)
→ SHOP_PHASE (after fighter selected)
→ FIGHTING (when both players ready)
→ VIEWING_REPLAY (after batch complete)
→ SHOP_PHASE (after replays viewed)
↑_______________________|

### Phase-Specific Handlers

Each phase handles specific UI and logic:

**ConnectionPhase:**
- Shows connection status
- Displays loading screen

**MatchmakingPhase:**
- Shows queue position
- Displays searching animation

**FighterSelectionPhase:**
- Displays fighter options
- Handles fighter selection
- Calls GameController.request_fighter_selection()

**ShopPhase:**
- Displays shop items and inventory
- Handles purchases via GameController.request_item_purchase()
- Handles refresh via GameController.request_shop_refresh()
- Completes via GameController.complete_shop_phase()

**FightingPhase:**
- Shows fight progress
- Displays opponent information
- Waits for batch completion

**ReplayViewingPhase:**
- Plays fight replays
- Handles navigation
- Calls GameController.notify_replay_viewed()

---

## Data Management

### Data Flow Hierarchy

Static Data (StaticDataManager)
├── Items Database
├── Fighter Database
└── Game Constants

Session Data (GameDataStore)
├── Fighter Selection
├── Current Resources (Gold)
├── Inventory
├── Battle Statistics
└── Current Shop State

Runtime Data (Phase-specific)
├── UI State
├── Animations
└── Temporary Values

### Data Update Pattern

1. Server sends update (e.g., purchase_result)
2. GameController processes message
3. GameDataStore updated with new values
4. GameDataStore emits relevant signal
5. All listening components update

Example:

_handle_purchase_result(data)
→ GameDataStore.set_gold(data.remaining_gold)
→ gold_changed signal emitted
→ ShopPhase._on_gold_changed() updates UI
→ UI shows new gold amount

---

## Message Routing

### Message Type Mapping

GameController._on_message_received() routes based on message.type:

- "connected" → _handle_connected_message()
- "matchmaking_started" → _handle_matchmaking_started()
- "match_found" → _handle_match_found()
- "fighter_selection_ready" → _handle_fighter_selection_ready()
- "purchase_result" → _handle_purchase_result()
- "shop_phase_start" → _handle_shop_phase_start()
- "fight_starting" → _handle_fight_starting()
- "batch_completed" → _handle_batch_completed()
- "replay_data" → _handle_replay_data()
- "waiting_for_opponent" → _handle_waiting_for_opponent()
- "opponent_ready" → _handle_opponent_ready()
- "error" → _handle_error()

### Phase-Routed Messages

Some messages are forwarded to current phase after processing:

_route_message_to_phase(message)
→ Checks current_phase_instance exists
→ Calls phase-specific handler if available

Examples:
- purchase_result → ShopPhase.handle_purchase_result()
- replay_data → ReplayViewingPhase.handle_replay_data()
- opponent_ready → Current phase shows notification

---

## Key Patterns

### Singleton Access
# Access global singletons from any script
GameDataStore.set_gold(1000)
StaticDataManager.get_item_data("sword_iron")

### Signal Connection
# In _ready() of any component
GameDataStore.gold_changed.connect(_on_gold_changed)

### Phase Communication
# Phases call GameController methods
get_parent().get_parent().get_node("GameController").request_item_purchase(item_id)
# Or store reference in phase._ready()
@onready var game_controller = $"/root/Main/GameController"

### Error Handling
# All errors from server go through
GameController._handle_error(data)
→ Show notification
→ Log error
→ Potentially transition to safe state