# SERVER_README.md

# Server-Client Communication Protocol

This document describes all interactions between the server and client in the auto-battling game. The game follows a phase-based architecture where clients progress through different game states.

**Important:** The server assumes clients have all static item and fighter data stored locally. Server only sends item/fighter IDs and dynamic state information.

## Table of Contents
1. [Connection Phase](#connection-phase)
2. [Matchmaking Phase](#matchmaking-phase)
3. [Fighter Selection Phase](#fighter-selection-phase)
4. [Shop Phase](#shop-phase)
5. [Fighting Phase](#fighting-phase)
6. [Replay Viewing Phase](#replay-viewing-phase)
7. [Error Handling](#error-handling)
8. [Disconnection Handling](#disconnection-handling)

---

## Connection Phase

**Purpose:** Establish WebSocket connection and register client with server.

### Client → Server

{
    "type": "connect",
    "client_id": "godot_client_12345678"
}

### Server → Client

{
    "type": "connected",
    "client_id": "godot_client_12345678",
    "starting_gold": 1000,
    "message": "Welcome! Entering matchmaking..."
}

**Next Phase:** Automatically transitions to Matchmaking Phase

---

## Matchmaking Phase

**Purpose:** Match two players together for a game session.

### Server → Client (Queue Entry)

{
    "type": "matchmaking_started",
    "queue_position": 1,
    "message": "Searching for opponent..."
}

### Server → Client (Match Found)

{
    "type": "match_found",
    "match_id": "match_12345678_87654321",
    "opponent": {
        "id": "godot_client_87654321",
        "name": "Player 2"
    },
    "message": "Match found! Opponent: Player 2"
}

**Next Phase:** Automatically transitions to Fighter Selection Phase

---

## Fighter Selection Phase

**Purpose:** Choose fighter and learning style before entering the shop.

### Server → Client

{
    "type": "fighter_selection_ready",
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

### Client → Server

{
    "type": "purchase_option",
    "option_id": "fighter_aggressive"
}

### Server → Client

{
    "type": "purchase_result",
    "success": true,
    "fighter_id": "fighter_aggressive",
    "remaining_gold": 1000,
    "reason": "Fighter selected successfully"
}

**Next Phase:** Automatically transitions to Shop Phase

---

## Shop Phase

**Purpose:** Purchase items and equipment. Used both after fighter selection and between fight batches.

### Server → Client (Shop Start)

{
    "type": "shop_phase_start",
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
    "refresh_cost": 10,
    "inventory": {
        "weapons": [],
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
    "message": "Welcome to the shop! Purchase items to strengthen your fighter."
}

**Note:** The message field will say "Shop refreshed after battle!" for subsequent shops.

### Shop Actions

#### Client → Server (Purchase Item)

{
    "type": "purchase_option",
    "option_id": "weapons_sword_iron_sword"
}

#### Server → Client (Purchase Result)

{
    "type": "purchase_result",
    "success": true,
    "item_id": "weapons_sword_iron_sword",
    "cost": 100,
    "remaining_gold": 900,
    "reason": "Purchase successful"
}

**Note:** Server does NOT automatically resend shop items after purchase. Client should update its local shop state.

#### Client → Server (Refresh Shop)

{
    "type": "refresh_shop"
}

#### Server → Client (Refresh Result - Success)

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

#### Server → Client (Refresh Result - Failure)

{
    "type": "refresh_result",
    "success": false,
    "remaining_gold": 5,
    "message": "Not enough gold to refresh shop"
}

#### Client → Server (Request Options)

{
    "type": "request_options"
}

#### Server → Client (Options Response)

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

### Shop Completion

#### Client → Server

{
    "type": "shop_phase_complete"
}

#### Server → Client (Waiting)

{
    "type": "waiting_for_opponent",
    "message": "You're ready! Waiting for opponent to finish shopping..."
}

#### Server → Client (Opponent Ready)

{
    "type": "opponent_ready",
    "message": "Your opponent is ready!"
}

**Next Phase:** Transitions to Fighting Phase when both players ready

---

## Fighting Phase

**Purpose:** Execute batch of fights between matched players.

### Server → Client (Fight Start)

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

### Server → Client (Batch Complete)

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

**Next Phase:** Automatically transitions to Replay Viewing Phase

---

## Replay Viewing Phase

**Purpose:** View recorded fight replays from the batch.

### Server → Client (Initial Replay)

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

### Navigation Commands

#### Client → Server (Auto-advance)

{
    "type": "replay_viewed"
}

#### Client → Server (Manual Navigation)

{
    "type": "request_next_replay",
    "current_index": 0
}

{
    "type": "request_previous_replay",
    "current_index": 1
}

{
    "type": "request_replay_list"
}

{
    "type": "request_replay_by_index",
    "index": 3
}

### Server Responses

#### Next/Previous Replay

{
    "type": "replay_next",
    "replay_data": {...},
    "replay_index": 1,
    "total_replays": 5,
    "is_final_replay": false,
    "batch_id": "batch_20240101_123456"
}

#### Replay List

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

**Next Phase:** Transitions to Shop Phase after viewing all replays

---

## Error Handling

### Server → Client

{
    "type": "error",
    "message": "Detailed error description",
    "error_code": "INVALID_PHASE"
}

### Common Error Codes
- `INVALID_PHASE` - Action not allowed in current phase
- `MISSING_ITEM_ID` - No item ID provided in request
- `NO_OPPONENT` - Opponent not found or disconnected
- `BATCH_ERROR` - Error during fight batch execution
- `INVALID_REPLAY_INDEX` - Requested replay index out of bounds
- `END_OF_REPLAYS` - Already at the last replay
- `START_OF_REPLAYS` - Already at the first replay
- `NO_BATCH_REPLAYS` - No batch replays available

---

## Disconnection Handling

### Client → Server

{
    "type": "disconnect"
}

### Server → Other Client

{
    "type": "opponent_disconnected",
    "message": "Your opponent disconnected. Returning to matchmaking..."
}

**Recovery:** Disconnected clients can reconnect and will be placed back in matchmaking.

---

## Key Implementation Notes

1. **Phase Flow:** Connection → Matchmaking → Fighter Selection → Shop → Fighting → Replay → Shop (loop)

2. **Item Data:** Server only sends item IDs and dynamic state (cost, stock, affordability, purchase status). Client must have full item data stored locally.

3. **Shop Updates:** Server does NOT automatically resend shop after purchases. Client must update its local shop state when receiving purchase confirmations.

4. **Refresh Shop:** On successful refresh, server sends new item list with minimal data. On failure, only sends error without item data.

5. **Fighter Selection:** Now a separate phase before the first shop. Server only sends fighter IDs and names. Client must have full fighter data stored locally.

6. **Inventory Format:** Server sends current inventory state with item IDs and equipped status. Client resolves full item properties from local data.

7. **Shop Message:** First shop after fighter selection shows "Welcome to the shop!" while subsequent shops show "Shop refreshed after battle!"