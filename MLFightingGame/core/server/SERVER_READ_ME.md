# SERVER_README.md

# Server-Client Communication Protocol

This document describes all interactions between the server and client in the auto-battling game. The game follows a phase-based architecture where clients progress through different game states.

**Important:** The server assumes clients have all static item and fighter data stored locally. Server only sends item/fighter IDs and dynamic state information.

## Table of Contents
1. [Connection Phase](#connection-phase)
2. [Matchmaking Phase](#matchmaking-phase)
3. [Initial Shop Phase](#initial-shop-phase)
4. [Fighting Phase](#fighting-phase)
5. [Replay Viewing Phase](#replay-viewing-phase)
6. [Shop Phase](#shop-phase)
7. [Error Handling](#error-handling)
8. [Disconnection Handling](#disconnection-handling)

---

## Connection Phase

**Purpose:** Establish WebSocket connection and register client with server.

### Client → Server
```json
{
    "type": "connect",
    "client_id": "godot_client_12345678"
}
Server → Client
json
{
    "type": "connected",
    "client_id": "godot_client_12345678",
    "starting_gold": 1000,
    "message": "Welcome! Entering matchmaking..."
}
Next Phase: Automatically transitions to Matchmaking Phase

Matchmaking Phase
Purpose: Match two players together for a game session.

Server → Client (Queue Entry)
json
{
    "type": "matchmaking_started",
    "queue_position": 1,
    "message": "Searching for opponent..."
}
Server → Client (Match Found)
json
{
    "type": "match_found",
    "match_id": "match_12345678_87654321",
    "opponent": {
        "id": "godot_client_87654321",
        "name": "Player 2"
    },
    "message": "Match found! Opponent: Player 2"
}
Next Phase: Automatically transitions to Initial Shop Phase

Initial Shop Phase
Purpose: Fighter selection and initial item purchases.

Stage 1: Fighter Selection

Server → Client
json
{
    "type": "initial_shop_ready",
    "phase": "fighter_selection",
    "fighter_options": [
        {
            "option_id": "fighter_aggressive",
            "fighter_name": "Aggressive Fighter"
        },
        {
            "option_id": "fighter_defensive",
            "fighter_name": "Defensive Fighter"
        },
        {
            "option_id": "fighter_balanced",
            "fighter_name": "Balanced Fighter"
        }
    ],
    "message": "Choose your fighter and learning style"
}
Client → Server
json
{
    "type": "purchase_option",
    "option_id": "fighter_aggressive"
}
Server → Client
json
{
    "type": "purchase_result",
    "success": true,
    "fighter_id": "fighter_aggressive",
    "remaining_gold": 1000,
    "reason": "Fighter selected successfully"
}
Note: After fighter selection, server automatically transitions to item shop and sends "options" message.

Stage 2: Initial Item Shop
Server → Client
json
{
    "type": "options",
    "data": [
        {
            "id": "weapons_sword_iron_sword",
            "cost": 100,
            "stock": 10,
            "can_afford": true,
            "already_purchased": false
        },
        {
            "id": "armour_light_leather_armour",
            "cost": 150,
            "stock": 5,
            "can_afford": true,
            "already_purchased": false
        },
        {
            "id": "learning_modifiers_epsilon_basic_increase",
            "cost": 60,
            "stock": 18,
            "can_afford": true,
            "already_purchased": false
        }
    ],
    "client_gold": 1000,
    "refresh_cost": 10
}
Client → Server (Purchase Item)
json
{
    "type": "purchase_option",
    "option_id": "weapons_sword_iron_sword",
    "auto_equip": false
}
Server → Client (Purchase Result)
json
{
    "type": "purchase_result",
    "success": true,
    "item_id": "weapons_sword_iron_sword",
    "cost": 100,
    "remaining_gold": 900,
    "reason": "Purchase successful"
}
Note: Server does NOT automatically resend shop items after purchase. Client should update its local shop state.

Stage 3: Shop Completion
Client → Server
json
{
    "type": "initial_shop_complete"
}
Server → Client (Waiting)
json
{
    "type": "waiting_for_opponent",
    "message": "You're ready! Waiting for opponent to finish shopping..."
}
Server → Client (Opponent Ready)
json
{
    "type": "opponent_ready",
    "message": "Your opponent is ready!"
}
Next Phase: Transitions to Fighting Phase when both players ready

Fighting Phase
Purpose: Execute batch of fights between matched players.

Server → Client (Fight Start)
json
{
    "type": "fight_starting",
    "batch_id": "batch_20240101_123456",
    "total_fights": 50,
    "recorded_fights": 5,
    "opponent": {
        "name": "Aggressive Fighter",
        "level": 1,
        "wins": 0,
        "losses": 0
    },
    "message": "Starting batch of fights. Results will be available soon."
}
Server → Client (Batch Complete)
json
{
    "type": "batch_completed",
    "batch_id": "batch_20240101_123456",
    "total_fights": 50,
    "wins": 30,
    "losses": 20,
    "win_rate": 0.6,
    "recorded_replays": 5,
    "message": "Batch complete! Win rate: 60.0%"
}
Next Phase: Automatically transitions to Replay Viewing Phase

Replay Viewing Phase
Purpose: View recorded fight replays from the batch.

Server → Client (Initial Replay)
json
{
    "type": "replay_data",
    "batch_summary": {
        "total_fights": 50,
        "wins": 30,
        "losses": 20,
        "win_rate": 0.6,
        "recorded_fights": 5,
        "current_replay_index": 0
    },
    "replay_data": {
        "metadata": {
            "w": 1,
            "d": 45.2,
            "tf": 2260,
            "ts": "2024-01-01T12:34:56"
        },
        "frames": [...]
    },
    "replay_index": 0,
    "total_replays": 5,
    "is_final_replay": false
}
Navigation Commands
Client → Server (Auto-advance)
json
{
    "type": "replay_viewed"
}
Client → Server (Manual Navigation)
json
{
    "type": "request_next_replay",
    "current_index": 0
}
json
{
    "type": "request_previous_replay",
    "current_index": 1
}
json
{
    "type": "request_replay_list"
}
json
{
    "type": "request_replay_by_index",
    "index": 3
}
Server Responses
Next/Previous Replay
json
{
    "type": "replay_next",
    "replay_data": {...},
    "replay_index": 1,
    "total_replays": 5,
    "is_final_replay": false,
    "batch_id": "batch_20240101_123456"
}
Replay List
json
{
    "type": "replay_list",
    "replays": [
        {
            "index": 0,
            "fight_number": 10,
            "winner": 1,
            "duration_seconds": 45.2,
            "total_frames": 2260,
            "timestamp": "2024-01-01T12:34:56"
        }
    ],
    "total_replays": 5,
    "current_index": 0,
    "batch_id": "batch_20240101_123456"
}
Next Phase: Transitions to Shop Phase after viewing all replays

Shop Phase
Purpose: Purchase items and equipment between fight batches.

Server → Client (Shop Start)
json
{
    "type": "shop_phase_start",
    "data": [
        {
            "id": "weapons_sword_steel_sword",
            "cost": 250,
            "stock": 5,
            "can_afford": true,
            "already_purchased": false
        },
        {
            "id": "armour_heavy_iron_armour",
            "cost": 300,
            "stock": 3,
            "can_afford": false,
            "already_purchased": false
        }
    ],
    "client_gold": 1150,
    "refresh_cost": 10,
    "inventory": {
        "weapons": [
            {
                "item_id": "weapons_sword_iron_sword",
                "equipped": true,
                "index": 0
            }
        ],
        "armour": [],
        "features": [],
        "reward_modifiers": {},
        "learning_modifiers": {}
    },
    "fighter_id": "aggressive",
    "learning_parameters": {
        "epsilon": 0.5,
        "decay": 0.005,
        "learning_rate": 0.002
    },
    "message": "Shop refreshed after battle!"
}
Shop Actions
Client → Server (Purchase)
json
{
    "type": "purchase_option",
    "option_id": "weapons_sword_steel_sword",
    "auto_equip": false
}
Server → Client (Purchase Result)
json
{
    "type": "purchase_result",
    "success": true,
    "item_id": "weapons_sword_steel_sword",
    "cost": 250,
    "remaining_gold": 900,
    "reason": "Purchase successful"
}
Note: Server does NOT resend shop items after purchase. Client updates local state.

Client → Server (Sell - Not Yet Implemented)
json
{
    "type": "sell_item",
    "item_id": "weapons_sword_iron_sword",
    "fighter_id": "aggressive"
}
Client → Server (Refresh)
json
{
    "type": "refresh_shop"
}
Server → Client (Refresh Result - Success)
json
{
    "type": "refresh_result",
    "success": true,
    "data": [
        {
            "id": "weapons_axe_battle_axe",
            "cost": 200,
            "stock": 4,
            "can_afford": true,
            "already_purchased": false
        }
    ],
    "remaining_gold": 890,
    "message": "Shop refreshed successfully"
}
Server → Client (Refresh Result - Failure)
json
{
    "type": "refresh_result",
    "success": false,
    "remaining_gold": 5,
    "message": "Not enough gold to refresh shop"
}
Client → Server (Request Options)
json
{
    "type": "request_options"
}
Server → Client (Options Response)
json
{
    "type": "options",
    "data": [
        {
            "id": "weapons_sword_steel_sword",
            "cost": 250,
            "stock": 5,
            "can_afford": true,
            "already_purchased": false
        }
    ],
    "client_gold": 890,
    "refresh_cost": 10
}
Client → Server (Get Status)
json
{
    "type": "get_status"
}
Server → Client (Status Response)
json
{
    "type": "status",
    "gold": 890,
    "items_owned": ["weapons_sword_iron_sword", "weapons_sword_steel_sword"],
    "total_purchases": 2
}
Shop Completion
Client → Server
json
{
    "type": "shop_phase_complete"
}
Server → Client (Waiting)
json
{
    "type": "waiting_for_opponent",
    "message": "You're ready! Waiting for opponent to finish shopping..."
}
Server → Client (Opponent Ready)
json
{
    "type": "opponent_ready",
    "message": "Your opponent is ready!"
}
Next Phase: Returns to Fighting Phase when both players ready

Error Handling
Server → Client
json
{
    "type": "error",
    "message": "Detailed error description",
    "error_code": "INVALID_PHASE"
}
Common Error Codes
INVALID_PHASE - Action not allowed in current phase
MISSING_ITEM_ID - No item ID provided in request
NO_OPPONENT - Opponent not found or disconnected
BATCH_ERROR - Error during fight batch execution
INVALID_REPLAY_INDEX - Requested replay index out of bounds
END_OF_REPLAYS - Already at the last replay
START_OF_REPLAYS - Already at the first replay
NO_BATCH_REPLAYS - No batch replays available
Disconnection Handling
Client → Server
json
{
    "type": "disconnect"
}
Server → Other Client
json
{
    "type": "opponent_disconnected",
    "message": "Your opponent disconnected. Returning to matchmaking..."
}
Recovery: Disconnected clients can reconnect and will be placed back in matchmaking.

Key Implementation Notes
Item Data: Server only sends item IDs and dynamic state (cost, stock, affordability, purchase status). Client must have full item data stored locally.

Shop Updates: Server does NOT automatically resend shop after purchases. Client must update its local shop state when receiving purchase confirmations.

Refresh Shop: On successful refresh, server sends new item list with minimal data. On failure, only sends error without item data.

Fighter Selection: Server only sends fighter IDs and names. Client must have full fighter data stored locally.

Inventory Format: Server sends current inventory state with item IDs and equipped status. Client resolves full item properties from local data.