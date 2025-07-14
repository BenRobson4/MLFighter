from enum import Enum

class ServerMessageType(Enum):
    """Messages sent from server to client"""
    # Connection messages
    CONNECTED = "connected"
    CONNECTION_ERROR = "connection_error"
    DISCONNECTED = "disconnected"
    OPPONENT_CONNECTED = "opponent_connected"
    OPPONENT_DISCONNECTED = "opponent_disconnected"
    
    # Game flow messages
    GAME_STATE_CHANGE = "game_state_change"
    MATCHMAKING_STARTED = "matchmaking_started"
    MATCH_FOUND = "match_found"
    FIGHTER_SELECTION_READY = "fighter_selection_ready"
    WAITING_FOR_OPPONENT = "waiting_for_opponent"
    OPPONENT_READY = "opponent_ready"
    FIGHT_STARTING = "fight_starting"
    BATCH_COMPLETED = "batch_completed" 
    REPLAY_DATA = "replay_data"
    SHOP_PHASE_START = "shop_phase_start"
    PLAYER_UPDATE = "player_update"
    GAME_ENDED = "game_ended"
    
    # Replay navigation messages
    REPLAY_NEXT = "replay_next" 
    REPLAY_PREVIOUS = "replay_previous"  
    REPLAY_LIST = "replay_list" 
    
    # Existing shop messages
    OPTIONS = "options"
    PURCHASE_RESULT = "purchase_result"
    REFRESH_RESULT = "refresh_result"
    PURCHASES_LIST = "purchases_list"

    STATUS = "status"  
    
    # Error messages
    ERROR = "error"


class ClientMessageType(Enum):
    """Messages sent from client to server"""
    # Connection messages
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Game flow messages
    FIGHTER_SELECTED = "fighter_selected"
    REPLAY_VIEWED = "replay_viewed"
    SHOP_PHASE_COMPLETE = "shop_phase_complete"
    
    # Replay navigation messages
    REQUEST_NEXT_REPLAY = "request_next_replay"  
    REQUEST_PREVIOUS_REPLAY = "request_previous_replay" 
    REQUEST_REPLAY_LIST = "request_replay_list"  
    REQUEST_REPLAY_BY_INDEX = "request_replay_by_index"  
    
    # Existing shop messages
    PURCHASE_OPTION = "purchase_option"
    REQUEST_OPTIONS = "request_options"
    REFRESH_SHOP = "refresh_shop"


class GamePhase(Enum):
    """Game phases that clients can be in"""
    CONNECTING = "connecting"
    MATCHMAKING = "matchmaking"
    FIGHTER_SELECTION = "fighter_selection"
    FIGHTING = "fighting"
    VIEWING_REPLAY = "viewing_replay"
    SHOP_PHASE = "shop_phase"
    GAME_OVER = "game_over"