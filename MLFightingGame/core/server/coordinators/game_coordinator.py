import asyncio
from typing import Dict, Any, Optional
from ..session.client_session import ClientSession
from ..protocols.message_types import GamePhase, ServerMessageType, ClientMessageType
from ...players import Player
from ...shop import ShopManager
from ...game_loop import GameManager, GameEngine
from ...globals.constants import ITEM_DIRECTORY, STARTING_GOLD
import logging
import datetime

logger = logging.getLogger(__name__)


class GameCoordinator:
    """
    Central coordinator that manages ALL game logic and flow.
    Receives messages from ConnectionManager and handles all game operations.
    """
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}  # client_id -> ClientSession
        self.connection_manager = None  # Will be injected
        # Initialize ShopManager with proper items directory
        self.shop_manager = ShopManager(
            starting_gold=STARTING_GOLD, 
            items_directory=ITEM_DIRECTORY
        )
        self.game_engine: GameEngine = None 
        self.opponent_pairs = {}  # client_id -> opponent_client_id mapping for fights
        self.game_manager = GameManager()  # Handles fight logic and replays

        # Matchmaking system
        self.matchmaking_queue = []  # List of client_ids waiting for match
        self.active_matches = {}  # match_id -> {client_1, client_2}
        self.client_to_match = {}  # client_id -> match_id
        
    def set_connection_manager(self, connection_manager):
        """Inject the connection manager for sending messages"""
        self.connection_manager = connection_manager
        
    # ==================== CLIENT LIFECYCLE ====================
    
    async def on_client_connected(self, client_id: str, websocket):
        """
        Entry point when a new client connects
        Imediately enters MATCHMAKING for now
        """
        logger.info(f"Client {client_id} connecting...")
        
        # Create session
        session = ClientSession(
            client_id=client_id,
            current_phase=GamePhase.CONNECTING
        )
        self.sessions[client_id] = session
        
        # Register with shop manager (prepare their resources)
        self.shop_manager.register_client(client_id)
        
        # Send welcome
        await self.send_to_client(client_id, {
            "type": ServerMessageType.CONNECTED.value,
            "client_id": client_id,
            "starting_gold": self.shop_manager.get_client_gold(client_id),
            "message": "Welcome! Entering matchmaking..."
        })
        
        # Enter matchmaking immediately
        await self.transition_client_phase(client_id, GamePhase.MATCHMAKING)
    

    async def on_client_disconnected(self, client_id: str):
        """Cleanup when client disconnects"""
        logger.info(f"Client {client_id} disconnecting...")
        
        # Remove from matchmaking queue if present
        if client_id in self.matchmaking_queue:
            self.matchmaking_queue.remove(client_id)
            logger.info(f"Removed {client_id} from matchmaking queue")
        
        # Handle if they were in a match
        if client_id in self.client_to_match:
            opponent_id = self.get_opponent_id(client_id)  # Use helper
            
            if opponent_id and opponent_id in self.sessions:
                await self.send_to_client(opponent_id, {
                    "type": ServerMessageType.OPPONENT_DISCONNECTED.value,
                    "message": "Your opponent disconnected. Returning to matchmaking..."
                })
                
                # Return opponent to matchmaking
                await self.transition_client_phase(opponent_id, GamePhase.MATCHMAKING)
            
            # Clean up match data
            match_id = self.client_to_match[client_id]
            if match_id in self.active_matches:
                del self.active_matches[match_id]
            
            # Clean up client_to_match entries
            if client_id in self.client_to_match:
                del self.client_to_match[client_id]
            if opponent_id and opponent_id in self.client_to_match:
                del self.client_to_match[opponent_id]
                    
        # Get the session if it exists
        session = self.sessions.get(client_id)
        
        if session:
            # Save player progress if they had created a player
            if session.player:
                # Log final stats
                stats = session.player.get_stats()
                logger.info(f"Client {client_id} final stats: "
                        f"Fights: {session.fights_completed}, "
                        f"Gold: {self.shop_manager.get_client_gold(client_id)}, "
                        f"Win rate: {stats.get('win_rate', 0):.2%}")
                
                # TODO: Save to database or file if you want persistence
                # session.player.save(f"saves/player_{client_id}.json")
            
            # Clean up any in-progress fight
            if session.current_phase == GamePhase.FIGHTING:
                logger.warning(f"Client {client_id} disconnected during fight")
                # TODO: Handle abandoned fights (maybe auto-loss?)
            
            # Remove the session
            del self.sessions[client_id]
            
            # Note: We don't remove from shop_manager in case they reconnect
            # You could add a timeout system to clean up after extended disconnection
            
        logger.info(f"Client {client_id} cleanup complete")
    
    # ==================== MESSAGE ROUTING ====================
    
    async def handle_client_message(self, client_id: str, message: dict):
        """
        Main message router - handles ALL incoming client messages
        """
        session = self.sessions.get(client_id)
        if not session:
            return
                
        msg_type = message.get("type")
        
        # Route messages based on type
        if msg_type == "purchase_option":
            await self.handle_purchase_message(client_id, message)
            
        elif msg_type == "request_options":
            await self.handle_options_request(client_id, message)
            
        elif msg_type == "refresh_shop":
            await self.handle_refresh_request(client_id, message)
            
        elif msg_type == "get_purchases":
            await self.handle_purchases_request(client_id, message)
            
        elif msg_type == "get_status":
            await self.handle_status_request(client_id, message)
            
        elif msg_type == ClientMessageType.INITIAL_SHOP_COMPLETE.value:
            if session.current_phase == GamePhase.INITIAL_SHOP:
                await self._handle_initial_shop_complete(session)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.INITIAL_SHOP}", "INVALID_PHASE")

        elif msg_type == ClientMessageType.REPLAY_VIEWED.value:
            if session.current_phase == GamePhase.VIEWING_REPLAY:
                await self._handle_replay_viewed(session)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.VIEWING_REPLAY}", "INVALID_PHASE")

        
        elif msg_type == ClientMessageType.REQUEST_NEXT_REPLAY.value:
            if session.current_phase == GamePhase.VIEWING_REPLAY:
                await self._handle_next_replay_request(session, message)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.VIEWING_REPLAY}", "INVALID_PHASE")
                    
        elif msg_type == ClientMessageType.REQUEST_PREVIOUS_REPLAY.value:
            if session.current_phase == GamePhase.VIEWING_REPLAY:
                await self._handle_previous_replay_request(session, message)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.VIEWING_REPLAY}", "INVALID_PHASE")
                    
        elif msg_type == ClientMessageType.REQUEST_REPLAY_LIST.value:
            if session.current_phase == GamePhase.VIEWING_REPLAY:
                await self._handle_replay_list_request(session)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.VIEWING_REPLAY}", "INVALID_PHASE")
                    
        elif msg_type == ClientMessageType.REQUEST_REPLAY_BY_INDEX.value:
            if session.current_phase == GamePhase.VIEWING_REPLAY:
                await self._handle_replay_by_index_request(session, message)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.VIEWING_REPLAY}", "INVALID_PHASE")
                    
        elif msg_type == ClientMessageType.SHOP_PHASE_COMPLETE.value:
            if session.current_phase == GamePhase.SHOP_PHASE:
                await self._handle_shop_phase_complete(session)
            else:
                await self.send_error(client_id, f"Current phase: {session.current_phase}, expected phase: {GamePhase.SHOP_PHASE}", "INVALID_PHASE")

        else:
            logger.warning(f"Unknown message type: {msg_type}")
            await self.send_error(client_id, f"Unknown message type: {msg_type}")
    
    # ==================== ERROR HANDLING ====================
    
    async def send_error(self, client_id: str, message: str, error_code: str = None):
        """Central error handling function"""
        error_data = {
            "type": ServerMessageType.ERROR.value,
            "message": message
        }
        
        if error_code:
            error_data["error_code"] = error_code
            
        logger.warning(f"Error for client {client_id}: {message} ({error_code or 'no code'})")
        await self.send_to_client(client_id, error_data)
    
    # ==================== SHOP MESSAGE HANDLERS ====================
    
    async def handle_purchase_message(self, client_id: str, data: Dict[str, Any]):
        """Handle purchase request"""
        session = self.sessions.get(client_id)
        if not session:
            return
            
        item_id = data.get("option_id")
        
        if not item_id:
            await self.send_error(client_id, "No item ID provided", "MISSING_ITEM_ID")
            return
        
        # Check if this is fighter selection (initial shop phase with no player yet)
        if session.current_phase == GamePhase.INITIAL_SHOP and not session.player:
            await self.handle_fighter_selection(client_id, data)
            return
            
        # Otherwise, process regular item purchase
        success, reason, purchase = self.shop_manager.process_purchase(client_id, item_id)
        
        # Send result
        await self.send_to_client(client_id, {
            "type": ServerMessageType.PURCHASE_RESULT.value,
            "success": success,
            "item_id": item_id,
            "cost": purchase.get("cost", 0) if purchase else 0,
            "remaining_gold": self.shop_manager.get_client_gold(client_id),
            "reason": reason
        })
            
    async def handle_refresh_request(self, client_id: str, data: Dict[str, Any]):
        """Handle shop refresh request"""
        success, message = self.shop_manager.refresh_shop(client_id)
        
        if success:
            # Get refreshed shop items
            shop_items = self.shop_manager.get_current_shop_items(client_id)
            
            # Strip down to essential data
            minimal_items = []
            for item in shop_items:
                minimal_items.append({
                    "id": item["id"],
                    "cost": item["cost"],
                    "stock": item.get("stock_remaining", item.get("stock", 0)),
                    "can_afford": item.get("can_afford", False),
                    "already_purchased": item.get("already_purchased", False)
                })
            
            # Send refresh result with new items
            await self.send_to_client(client_id, {
                "type": ServerMessageType.REFRESH_RESULT.value,
                "success": success,
                "data": minimal_items,
                "remaining_gold": self.shop_manager.get_client_gold(client_id),
                "message": message
            })
        else:
            # Send refresh failure
            await self.send_to_client(client_id, {
                "type": ServerMessageType.REFRESH_RESULT.value,
                "success": success,
                "remaining_gold": self.shop_manager.get_client_gold(client_id),
                "message": message
            })
        
    async def handle_options_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for available options"""
        shop_items = self.shop_manager.get_current_shop_items(client_id)
        
        # Strip down to essential data only
        minimal_items = []
        for item in shop_items:
            minimal_items.append({
                "id": item["id"],
                "cost": item["cost"],
                "stock": item.get("stock_remaining", item.get("stock", 0)),
                "can_afford": item.get("can_afford", False),
                "already_purchased": item.get("already_purchased", False)
            })
        
        await self.send_to_client(client_id, {
            "type": ServerMessageType.OPTIONS.value,
            "data": minimal_items,
            "client_gold": self.shop_manager.get_client_gold(client_id),
            "refresh_cost": ShopManager.REFRESH_COST
        })
        
    async def handle_purchases_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for purchase history"""
        summary = self.shop_manager.get_purchase_summary(client_id)
        
        await self.send_to_client(client_id, {
            "type": ServerMessageType.PURCHASES_LIST.value,
            "purchases": summary["purchase_history"],
            "total_spent": summary["total_spent"],
            "items_owned": summary["items_owned"]
        })
        
    async def handle_status_request(self, client_id: str, data: Dict[str, Any]):
        """Handle request for client status"""
        summary = self.shop_manager.get_purchase_summary(client_id)
        
        await self.send_to_client(client_id, {
            "type": ServerMessageType.STATUS.value,
            "gold": summary["remaining_gold"],
            "items_owned": summary["items_owned"],
            "total_purchases": summary["total_purchases"]
        })

    async def _handle_initial_shop_complete(self, session: ClientSession):
        """Handle when a player completes their initial shop"""
        client_id = session.client_id
        
        # Mark this player as ready
        session.ready_for_next_phase = True
        session.initial_shop_complete = True
        
        # Get opponent
        opponent_id = self.get_opponent_id(client_id)
        if not opponent_id:
            logger.error(f"No opponent found for {client_id} during initial shop complete")
            return
        
        opponent_session = self.sessions.get(opponent_id)
        if not opponent_session:
            logger.error(f"No session found for opponent {opponent_id}")
            return
        
        # Notify this player they're ready
        await self.send_to_client(client_id, {
            "type": ServerMessageType.WAITING_FOR_OPPONENT.value,
            "message": "You're ready! Waiting for opponent to finish shopping..."
        })
        
        # Notify opponent that this player is ready
        await self.send_to_client(opponent_id, {
            "type": ServerMessageType.OPPONENT_READY.value,
            "message": f"Your opponent is ready!"
        })
        
        # Check if both players are ready
        if session.ready_for_next_phase and opponent_session.ready_for_next_phase:
            # Reset ready flags for next phase
            session.ready_for_next_phase = False
            opponent_session.ready_for_next_phase = False
            
            # Both ready - transition both to fighting
            logger.info(f"Both players ready - starting fight phase for match {self.client_to_match.get(client_id)}")
            
            # Small delay to ensure clients receive the ready messages
            await asyncio.sleep(0.5)
            
            # Transition both players
            await self.transition_client_phase(client_id, GamePhase.FIGHTING)
            await self.transition_client_phase(opponent_id, GamePhase.FIGHTING)
        
    async def _handle_shop_phase_complete(self, session: ClientSession):
        """Handle when a player completes their shop phase"""
        client_id = session.client_id
        
        # Mark this player as ready
        session.ready_for_next_phase = True
        
        # Get opponent
        opponent_id = self.get_opponent_id(client_id)
        if not opponent_id:
            logger.error(f"No opponent found for {client_id} during shop phase complete")
            return
        
        opponent_session = self.sessions.get(opponent_id)
        if not opponent_session:
            logger.error(f"No session found for opponent {opponent_id}")
            return
        
        # Notify players
        await self.send_to_client(client_id, {
            "type": ServerMessageType.WAITING_FOR_OPPONENT.value,
            "message": "You're ready! Waiting for opponent to finish shopping..."
        })
        
        await self.send_to_client(opponent_id, {
            "type": ServerMessageType.OPPONENT_READY.value,
            "message": f"Your opponent is ready!"
        })
        
        # Check if both players are ready
        if session.ready_for_next_phase and opponent_session.ready_for_next_phase:
            # Reset ready flags
            session.ready_for_next_phase = False
            opponent_session.ready_for_next_phase = False
            
            # IMPORTANT: Clear previous batch data for both players
            for s in [session, opponent_session]:
                s.current_batch_id = None
                s.batch_fights_completed = 0
                s.batch_wins = 0
                s.batch_losses = 0
                s.batch_recorded_replays = []
                s.current_replay = None
                s.current_replay_index = 0
                s.replay_viewed = False
            
            logger.info(f"Cleared batch data for both players, ready for new fight phase")
            
            if self._should_game_end(session):
                await self.transition_client_phase(client_id, GamePhase.GAME_OVER)
                await self.transition_client_phase(opponent_id, GamePhase.GAME_OVER)
            else:
                await self.transition_client_phase(client_id, GamePhase.FIGHTING)
                await self.transition_client_phase(opponent_id, GamePhase.FIGHTING)
            
    async def handle_fighter_selection(self, client_id: str, message: dict):
        """Handle fighter selection from client"""
        session = self.sessions.get(client_id)
        if not session:
            return
        
        option_id = message.get("option_id")
        success, msg, player_config = self.shop_manager.process_fighter_selection(client_id, option_id)
        
        if success:
            session.player = Player(
                player_id=0,
                fighter_name=player_config['fighter_name'],
                starting_gold=player_config['starting_gold'],
                starting_level=player_config['starting_level'],
                learning_parameters=player_config['learning_parameters'],
                initial_feature_mask=player_config.get('initial_feature_mask'), 
                items=player_config.get('starting_items'),
                num_actions=6,
                num_features=20
            )
            
            await self.send_to_client(client_id, {
                "type": ServerMessageType.PURCHASE_RESULT.value, 
                "success": True,
                "fighter_id": option_id,
                "remaining_gold": self.shop_manager.get_client_gold(client_id),
                "reason": "Fighter selected successfully"
            })
            
            await self._enter_shop_phase(session)
            
        else:
            # Send error
            await self.send_to_client(client_id, {
                "type": ServerMessageType.PURCHASE_RESULT.value,
                "success": False,
                "fighter_id": option_id,
                "remaining_gold": self.shop_manager.get_client_gold(client_id),
                "reason": msg
            })
    
    # ==================== PHASE TRANSITIONS ====================
    
    async def transition_client_phase(self, client_id: str, new_phase: GamePhase):
        """Main state machine - handles transitions between game phases"""
        session = self.sessions.get(client_id)
        if not session:
            return
            
        old_phase = session.current_phase
        session.current_phase = new_phase
        
        # Send phase change notification to client
        # await self.send_to_client(client_id, {
        #     "type": ServerMessageType.GAME_STATE_CHANGE,
        #     "phase": new_phase,
        #     "data": {...}
        # })
        
        # Execute phase entry logic
        if new_phase == GamePhase.MATCHMAKING:
            await self._enter_matchmaking(session)
        if new_phase == GamePhase.INITIAL_SHOP:
            await self._enter_initial_shop(session)
        elif new_phase == GamePhase.FIGHTING:
            await self._enter_fighting(session)
        elif new_phase == GamePhase.VIEWING_REPLAY:
            await self._enter_replay_viewing(session)
        elif new_phase == GamePhase.SHOP_PHASE:
            await self._enter_shop_phase(session)
        elif new_phase == GamePhase.GAME_OVER:
            await self._enter_game_over(session)
    
    # ==================== PHASE HANDLERS ====================

    async def _enter_matchmaking(self, session: ClientSession):
        """
        Enter matchmaking queue and wait for opponent
        """
        client_id = session.client_id
        
        # Add to queue
        self.matchmaking_queue.append(client_id)
        logger.info(f"Client {client_id} entered matchmaking. Queue size: {len(self.matchmaking_queue)}")
        
        # Notify client they're in queue
        await self.send_to_client(client_id, {
            "type": ServerMessageType.MATCHMAKING_STARTED.value,
            "queue_position": len(self.matchmaking_queue),
            "message": "Searching for opponent..."
        })
        
        # Try to make a match
        await self._try_make_match()

    async def _try_make_match(self):
        """Try to match players in queue"""
        # Need at least 2 players
        if len(self.matchmaking_queue) < 2:
            return
            
        # Take first 2 players from queue
        player1_id = self.matchmaking_queue.pop(0)
        player2_id = self.matchmaking_queue.pop(0)
        
        # Create match
        match_id = f"match_{player1_id[:8]}_{player2_id[:8]}"
        
        # Store match info
        self.active_matches[match_id] = {
            "client_1": player1_id,
            "client_2": player2_id,
            "created_at": datetime.datetime.now()
        }
        
        # Store reverse lookup
        self.client_to_match[player1_id] = match_id
        self.client_to_match[player2_id] = match_id
                
        logger.info(f"Match created: {match_id} ({player1_id} vs {player2_id})")
        
        # Notify both players
        await self._notify_match_found(player1_id, player2_id, match_id)
        
        # Transition both to initial shop
        await self.transition_client_phase(player1_id, GamePhase.INITIAL_SHOP)
        await self.transition_client_phase(player2_id, GamePhase.INITIAL_SHOP)
        
    async def _notify_match_found(self, player1_id: str, player2_id: str, match_id: str):
        """
        Notify both players that match was found
        """
        # Get opponent names if available
        p1_name = "Player 1"  # TODO: Get actual name
        p2_name = "Player 2"  # TODO: Get actual name
        
        # Notify player 1
        await self.send_to_client(player1_id, {
            "type": ServerMessageType.MATCH_FOUND.value,
            "match_id": match_id,
            "opponent": {
                "id": player2_id,
                "name": p2_name
            },
            "message": f"Match found! Opponent: {p2_name}"
        })
        
        # Notify player 2
        await self.send_to_client(player2_id, {
            "type": ServerMessageType.MATCH_FOUND.value,
            "match_id": match_id,
            "opponent": {
                "id": player1_id,
                "name": p1_name
            },
            "message": f"Match found! Opponent: {p1_name}"
        })
    
    async def _enter_initial_shop(self, session: ClientSession):
        """
        Start initial shop phase - fighter selection first, then items
        """
        # Generate fighter options
        fighter_options = self.shop_manager.generate_fighter_options(session.client_id)
        
        # Strip down to minimal fighter data
        minimal_fighters = []
        for fighter in fighter_options:
            minimal_fighters.append({
                "option_id": fighter["option_id"],
                "fighter_name": fighter["fighter_name"]
            })
        
        # Send fighter selection message
        await self.send_to_client(session.client_id, {
            "type": ServerMessageType.INITIAL_SHOP_READY.value,
            "phase": "fighter_selection",
            "fighter_options": minimal_fighters,
            "message": "Choose your fighter and learning style"
        })
    
    async def _enter_fighting(self, session: ClientSession):
        """
        Start fight phase between two matched players using GameManager
        Only one player should create and run the batch
        """
        
        # ==================== STEP 1: VALIDATE OPPONENT PAIRING ====================
        opponent_id = self.get_opponent_id(session.client_id)
        if not opponent_id:
            logger.error(f"No opponent found for client {session.client_id}")
            await self.send_error(session.client_id, "No opponent found. Returning to shop.", "NO_OPPONENT")
            await self.transition_client_phase(session.client_id, GamePhase.SHOP_PHASE)
            return
        
        opponent_session = self.sessions.get(opponent_id)
        if not opponent_session or not opponent_session.player:
            logger.error(f"Opponent {opponent_id} session or player not found")
            await self.send_error(session.client_id, "Opponent disconnected. Returning to shop.", "OPPONENT_DISCONNECTED")
            await self.transition_client_phase(session.client_id, GamePhase.SHOP_PHASE)
            return
        
        # ==================== STEP 2: DETERMINE PLAYER IDS ====================
        # Use consistent ordering - lower client_id is player 1 and runs the batch
        if session.client_id < opponent_id:
            should_run_batch = True
            session.player.set_player_id(1)
            opponent_session.player.set_player_id(2)
        else:
            should_run_batch = False
            session.player.set_player_id(2)
            opponent_session.player.set_player_id(1)
        
        # ==================== STEP 3: CHECK IF BATCH ALREADY EXISTS ====================
        # Check if opponent already created a batch
        if hasattr(opponent_session, 'current_batch_id') and opponent_session.current_batch_id:
            # Opponent already created batch, copy their batch data
            session.current_batch_id = opponent_session.current_batch_id
            session.batch_fights_completed = opponent_session.batch_fights_completed
            session.batch_wins = opponent_session.batch_losses  # Swap wins/losses
            session.batch_losses = opponent_session.batch_wins
            session.batch_recorded_replays = opponent_session.batch_recorded_replays
            session.current_replay = opponent_session.current_replay
            session.current_replay_index = opponent_session.current_replay_index
            session.replay_viewed = False
            
            logger.info(f"Client {session.client_id} joining existing batch {session.current_batch_id}")

            # IMPORTANT: Transition to replay viewing since batch is complete
            await self.transition_client_phase(session.client_id, GamePhase.VIEWING_REPLAY)
            return  # Don't run the batch again
        
        # ==================== STEP 4: CHECK IF WE ALREADY CREATED BATCH ====================
        if hasattr(session, 'current_batch_id') and session.current_batch_id:
            logger.info(f"Client {session.client_id} already has batch {session.current_batch_id}")
            return  # Already created, don't run again
        
        # ==================== STEP 5: ONLY ONE CLIENT CREATES AND RUNS BATCH ====================
        if not should_run_batch:
            # Wait a moment for the other client to create the batch
            await asyncio.sleep(0.5)
            
            # Check again if opponent created batch
            if hasattr(opponent_session, 'current_batch_id') and opponent_session.current_batch_id:
                # Copy their batch data
                session.current_batch_id = opponent_session.current_batch_id
                session.batch_fights_completed = opponent_session.batch_fights_completed
                session.batch_wins = opponent_session.batch_losses  # Swap wins/losses
                session.batch_losses = opponent_session.batch_wins
                session.batch_recorded_replays = opponent_session.batch_recorded_replays
                session.current_replay = opponent_session.current_replay
                session.current_replay_index = opponent_session.current_replay_index
                session.replay_viewed = False
                
                logger.info(f"Client {session.client_id} joined batch {session.current_batch_id} after waiting")
                return
            else:
                # Something went wrong, opponent didn't create batch
                logger.error(f"Expected opponent {opponent_id} to create batch but they didn't")
                return
        
        # ==================== STEP 6: THIS CLIENT CREATES THE BATCH ====================
        logger.info(f"Client {session.client_id} creating new batch")
        
        # Store opponent references
        session.current_opponent = opponent_session.player
        opponent_session.current_opponent = session.player
        
        # Initialize batch tracking
        batch_id = f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize for both clients BEFORE sending messages
        session.current_batch_id = batch_id
        session.batch_fights_completed = 0
        session.batch_wins = 0
        session.batch_losses = 0
        session.batch_recorded_replays = []
        
        opponent_session.current_batch_id = batch_id
        opponent_session.batch_fights_completed = 0
        opponent_session.batch_wins = 0
        opponent_session.batch_losses = 0
        opponent_session.batch_recorded_replays = []
        
        # ==================== STEP 7: NOTIFY CLIENTS ====================
        # Send notification that fights are about to begin
        batch_start_message = {
            "type": ServerMessageType.FIGHT_STARTING.value,
            "batch_id": batch_id,
            "total_fights": 50,
            "recorded_fights": 5,
            "opponent": {
                "name": opponent_session.player.fighter.name,
                "level": opponent_session.player.level,
                "wins": opponent_session.player.wins,
                "losses": opponent_session.player.losses
            },
            "message": "Starting batch of fights. Results will be available soon."
        }
        
        await self.send_to_client(session.client_id, batch_start_message)
        
        # Send mirror message to opponent
        opponent_batch_message = {
            "type": ServerMessageType.FIGHT_STARTING.value,
            "batch_id": batch_id,
            "total_fights": 50,
            "recorded_fights": 5,
            "opponent": {
                "name": session.player.fighter.name,
                "level": session.player.level,
                "wins": session.player.wins,
                "losses": session.player.losses
            },
            "message": "Starting batch of fights. Results will be available soon."
        }
        
        await self.send_to_client(opponent_id, opponent_batch_message)
        
        # ==================== STEP 8: RUN THE BATCH ====================
        try:
            # Determine player positions
            if session.player.player_id == 1:
                client_1_id = session.client_id
                client_2_id = opponent_id
                player_1 = session.player
                player_2 = opponent_session.player
                local_is_player_1 = True
            else:
                client_1_id = opponent_id
                client_2_id = session.client_id
                player_1 = opponent_session.player
                player_2 = session.player
                local_is_player_1 = False
            
            logger.info(f"Starting batch {batch_id}: {client_1_id} vs {client_2_id}")

            # Run batch of 50 fights
            batch_results = await self.game_manager.run_fight_batch(
                client_1_id=client_1_id,
                client_2_id=client_2_id,
                player_1=player_1,
                player_2=player_2,
                num_fights=50,
                record_interval=10
            )
            
            # ==================== STEP 9: PROCESS RESULTS ====================
            # Update session with batch results
            if local_is_player_1:
                session.batch_wins = batch_results["client_1_wins"]
                session.batch_losses = batch_results["completed_fights"] - batch_results["client_1_wins"]
                opponent_session.batch_wins = batch_results["client_2_wins"]
                opponent_session.batch_losses = batch_results["completed_fights"] - batch_results["client_2_wins"]
            else:
                session.batch_wins = batch_results["client_2_wins"]
                session.batch_losses = batch_results["completed_fights"] - batch_results["client_2_wins"]
                opponent_session.batch_wins = batch_results["client_1_wins"]
                opponent_session.batch_losses = batch_results["completed_fights"] - batch_results["client_1_wins"]
            
            # Update fight counters
            session.batch_fights_completed = batch_results["completed_fights"]
            session.fights_completed += batch_results["completed_fights"]
            opponent_session.batch_fights_completed = batch_results["completed_fights"]
            opponent_session.fights_completed += batch_results["completed_fights"]
            
            # Store recorded replays
            session.batch_recorded_replays = batch_results["recorded_replays"]
            opponent_session.batch_recorded_replays = batch_results["recorded_replays"]
            
            # Store latest replay
            if batch_results["recorded_replays"]:
                session.current_replay = batch_results["recorded_replays"][-1]
                opponent_session.current_replay = batch_results["recorded_replays"][-1]
                session.current_replay_index = len(batch_results["recorded_replays"]) - 1
                opponent_session.current_replay_index = len(batch_results["recorded_replays"]) - 1
            
            session.replay_viewed = False
            opponent_session.replay_viewed = False
            
            # Update player statistics
            session.player.end_batch(session.batch_wins, session.batch_losses)
            opponent_session.player.end_batch(opponent_session.batch_wins, opponent_session.batch_losses)
            
            # ==================== STEP 10: NOTIFY COMPLETION ====================
            duration = (batch_results["end_time"] - batch_results["start_time"]).total_seconds()
            logger.info(f"Batch {batch_id} completed in {duration:.2f}s")
            
            # Send completion notifications
            local_win_rate = session.batch_wins / max(1, session.batch_fights_completed)
            await self.send_to_client(session.client_id, {
                "type": ServerMessageType.BATCH_COMPLETED.value,
                "batch_id": batch_id,
                "total_fights": session.batch_fights_completed,
                "wins": session.batch_wins,
                "losses": session.batch_losses,
                "win_rate": local_win_rate,
                "recorded_replays": len(session.batch_recorded_replays),
                "message": f"Batch complete! Win rate: {local_win_rate:.1%}"
            })
            
            opponent_win_rate = opponent_session.batch_wins / max(1, opponent_session.batch_fights_completed)
            await self.send_to_client(opponent_id, {
                "type": ServerMessageType.BATCH_COMPLETED.value,
                "batch_id": batch_id,
                "total_fights": opponent_session.batch_fights_completed,
                "wins": opponent_session.batch_wins,
                "losses": opponent_session.batch_losses,
                "win_rate": opponent_win_rate,
                "recorded_replays": len(opponent_session.batch_recorded_replays),
                "message": f"Batch complete! Win rate: {opponent_win_rate:.1%}"
            })

            # At the end of _enter_fighting, before transitions:
            logger.info(f"Batch {batch_id} complete, transitioning clients to replay viewing")
            logger.info(f"Session {session.client_id} has {len(session.batch_recorded_replays)} replays")
            logger.info(f"Opponent {opponent_id} has {len(opponent_session.batch_recorded_replays)} replays")

            # Transition to replay viewing
            await self.transition_client_phase(session.client_id, GamePhase.VIEWING_REPLAY)
            logger.info(f"Client {session.client_id} transitioned to replay viewing")

            await self.transition_client_phase(opponent_id, GamePhase.VIEWING_REPLAY)
            logger.info(f"Client {opponent_id} transitioned to replay viewing")
            
        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {e}", exc_info=True)
            
            # Notify both clients of the error
            await self.send_error(session.client_id, f"Fight batch encountered an error: {str(e)}", "BATCH_ERROR")
            await self.send_error(opponent_id, f"Fight batch encountered an error: {str(e)}", "BATCH_ERROR")
            
            # Clean up
            session.current_batch_id = None
            opponent_session.current_batch_id = None
            
            # Return to shop
            await self.transition_client_phase(session.client_id, GamePhase.SHOP_PHASE)
            await self.transition_client_phase(opponent_id, GamePhase.SHOP_PHASE)
                        
    async def _enter_replay_viewing(self, session: ClientSession):
        """Send batch replay data to client"""
        
        # Set the current replay index to 0 for the first replay
        session.current_replay_index = 0
        session.current_replay = session.batch_recorded_replays[0]
        
        # Create summary of batch results
        batch_summary = {
            "total_fights": session.batch_fights_completed,
            "wins": session.batch_wins,
            "losses": session.batch_losses,
            "win_rate": session.batch_wins / max(1, session.batch_fights_completed),
            "recorded_fights": len(session.batch_recorded_replays),
            "current_replay_index": 0,
        }
        
        # Send batch summary and first replay
        await self.send_to_client(session.client_id, {
            "type": ServerMessageType.REPLAY_DATA.value,
            "batch_summary": batch_summary,
            "replay_data": session.batch_recorded_replays[0],
            "replay_index": 0,
            "total_replays": len(session.batch_recorded_replays),
            "is_final_replay": len(session.batch_recorded_replays) == 1,
        })
        # Client will respond with REPLAY_VIEWED when done watching each replay, if REPLAY_VIEWED is sent on the final replay
        # then the client will transition to the shop phase.
        pass
    
    async def _enter_shop_phase(self, session: ClientSession):
        """
        Regular shop phase (not initial) - with free reroll
        """
        # Apply fight rewards first
        if session.current_replay:
            winner = session.current_replay.get("metadata", {}).get("winner", 0)
            gold_earned = 100 if winner == 1 else 50  # Example rewards
            self.shop_manager.add_gold_to_client(session.client_id, gold_earned)
        
        # Regenerate shop (free reroll after fight)
        self.shop_manager.regenerate_shop(session.client_id)
        
        # Get current inventory from player
        current_inventory = self._get_player_inventory(session)
        
        # Get shop items with minimal data
        shop_items = self.shop_manager.get_current_shop_items(session.client_id)
        minimal_items = []
        for item in shop_items:
            minimal_items.append({
                "id": item["id"],
                "cost": item["cost"],
                "stock": item.get("stock_remaining", item.get("stock", 0)),
                "can_afford": item.get("can_afford", False),
                "already_purchased": item.get("already_purchased", False)
            })
        
        # Send new shop with minimal data
        await self.send_to_client(session.client_id, {
            "type": ServerMessageType.SHOP_PHASE_START.value,
            "data": minimal_items,
            "client_gold": self.shop_manager.get_client_gold(session.client_id),
            "refresh_cost": ShopManager.REFRESH_COST,
            "inventory": current_inventory,
            "fighter_id": session.player.fighter.name,
            "learning_parameters": session.player.learning_parameters.to_dict(),
            "message": "Shop refreshed after battle!"
        })
        # Client will respond with SHOP_PHASE_COMPLETE

    def _get_player_inventory(self, session: ClientSession) -> dict:
        """Extract player inventory in format suitable for client"""
        if not session.player or not session.player.inventory:
            return {
                "weapons": [],
                "armour": [],
                "features": [],
                "reward_modifiers": {},
                "learning_modifiers": {}
            }
        
        inventory = session.player.inventory
        
        # Convert weapons to client format
        weapons_data = []
        for i, weapon in enumerate(inventory.weapons):
            weapons_data.append({
                "item_id": weapon.id,  # Server-generated ID like "weapons_sword_steel_sword"
                "equipped": weapon.equipped,
                "index": i
            })
        
        # Convert armour to client format
        armour_data = []
        for i, armour in enumerate(inventory.armour):
            armour_data.append({
                "item_id": armour.id,  # Server-generated ID like "armour_light_leather_armour"
                "equipped": armour.equipped,
                "index": i
            })
        
        return {
            "weapons": weapons_data,
            "armour": armour_data,
            "features": list(inventory.features),
            "reward_modifiers": inventory.reward_modifiers,
            "learning_modifiers": inventory.learning_modifiers
        }
    
    async def _enter_game_over(self, session: ClientSession):
        """
        Game ended
        - Send final stats
        - Save player progress
        - Clean up session
        """
        pass
    
    # ==================== REPLAY HANDLERS ====================

    async def _handle_replay_viewed(self, session: ClientSession):
        """Handle when client has finished viewing a replay (automatic progression)"""
        current_index = getattr(session, 'current_replay_index', 0)
        next_index = current_index + 1
        
        # If at end, transition to shop phase
        if next_index >= len(session.batch_recorded_replays):
            logger.info(f"Client {session.client_id} finished viewing all replays, transitioning to shop")
            await self.transition_client_phase(session.client_id, GamePhase.SHOP_PHASE)
        else:
            # Send next replay
            await self._send_replay_to_client(session, next_index, auto_advance=True)

    async def _handle_next_replay_request(self, session: ClientSession, message: dict):
        """Handle request for next replay in batch (manual button press)"""
        current_index = getattr(session, 'current_replay_index', 0)
        next_index = current_index + 1
        
        # If at end, send error
        if next_index >= len(session.batch_recorded_replays):
            await self.send_error(session.client_id, "Already at the last replay", "END_OF_REPLAYS")
        else:
            await self._send_replay_to_client(session, next_index, auto_advance=False)

    async def _handle_previous_replay_request(self, session: ClientSession, message: dict):
        """Handle request for previous replay in batch"""
        current_index = getattr(session, 'current_replay_index', 0)
        prev_index = current_index - 1
        
        # If at beginning, send error
        if prev_index < 0:
            await self.send_error(session.client_id, "Already at the first replay", "START_OF_REPLAYS")
        else:
            await self._send_replay_to_client(session, prev_index, auto_advance=False)

    async def _handle_replay_by_index_request(self, session: ClientSession, message: dict):
        """Handle request for specific replay by index"""
        requested_index = message.get("index", 0)
        
        # Validate index
        if not hasattr(session, 'batch_recorded_replays') or not session.batch_recorded_replays:
            await self.send_error(session.client_id, "No batch replays available", "NO_BATCH_REPLAYS")
            return
        
        if requested_index < 0 or requested_index >= len(session.batch_recorded_replays):
            await self.send_error(session.client_id, f"Invalid replay index: {requested_index}", "INVALID_REPLAY_INDEX")
            return
        
        await self._send_replay_to_client(session, requested_index, auto_advance=False)

    async def _send_replay_to_client(self, session: ClientSession, index: int, auto_advance: bool = False):
        """Central function to send a replay of specified index to the client"""
        if not hasattr(session, 'batch_recorded_replays') or not session.batch_recorded_replays:
            await self.send_error(session.client_id, "No batch replays available", "NO_BATCH_REPLAYS")
            return False
        
        # Validate index
        if index < 0 or index >= len(session.batch_recorded_replays):
            logger.error(f"Invalid replay index {index} for client {session.client_id}")
            await self.send_error(session.client_id, f"Invalid replay index: {index}", "INVALID_REPLAY_INDEX")
            return False
        
        # Get replay data
        replay_data = session.batch_recorded_replays[index]
        
        # Update session state
        session.current_replay = replay_data
        session.current_replay_index = index
        
        # Choose appropriate message type based on context
        if auto_advance:
            message_type = ServerMessageType.REPLAY_DATA.value
        elif index > getattr(session, 'current_replay_index', 0) - 1:
            message_type = ServerMessageType.REPLAY_NEXT.value
        elif index < getattr(session, 'current_replay_index', 0) + 1:
            message_type = ServerMessageType.REPLAY_PREVIOUS.value
        else:
            message_type = ServerMessageType.REPLAY_DATA.value
        
        # Send replay to client
        await self.send_to_client(session.client_id, {
            "type": message_type,
            "replay_data": replay_data,
            "replay_index": index,
            "total_replays": len(session.batch_recorded_replays),
            "is_final_replay": index == len(session.batch_recorded_replays) - 1,
            "batch_id": session.current_batch_id
        })
        
        logger.info(f"Client {session.client_id} sent replay {index + 1}/{len(session.batch_recorded_replays)}")
        return True

    async def _handle_replay_list_request(self, session: ClientSession):
        """Handle request for list of all replays in batch"""
        if not hasattr(session, 'batch_recorded_replays') or not session.batch_recorded_replays:
            await self.send_error(session.client_id, "No batch replays available", "NO_BATCH_REPLAYS")
            return
        
        # Create list of replay summaries
        replay_summaries = []
        for idx, replay in enumerate(session.batch_recorded_replays):
            metadata = replay.get("metadata", {})
            
            # Extract relevant metadata for list display
            summary = {
                "index": idx,
                "fight_number": (idx + 1) * 10,  # Fights 10, 20, 30, etc.
                "winner": metadata.get("w", 0),
                "duration_seconds": metadata.get("d", 0),
                "total_frames": metadata.get("tf", 0),
                "timestamp": metadata.get("ts", "")
            }
            replay_summaries.append(summary)
        
        # Send the list
        await self.send_to_client(session.client_id, {
            "type": ServerMessageType.REPLAY_LIST.value,
            "replays": replay_summaries,
            "total_replays": len(replay_summaries),
            "current_index": getattr(session, 'current_replay_index', 0),
            "batch_id": session.current_batch_id
        })
    
    # ==================== HELPER METHODS ====================

    def get_opponent_id(self, client_id: str) -> Optional[str]:
        """Get opponent ID for a given client"""
        match_id = self.client_to_match.get(client_id)
        if not match_id:
            return None
            
        match = self.active_matches.get(match_id)
        if not match:
            return None
            
        # Return the other client in the match
        if match["client_1"] == client_id:
            return match["client_2"]
        else:
            return match["client_1"]
    
    def _should_game_end(self, session: ClientSession) -> bool:
        """
        Determine if game should end
        - Max fights reached?
        - Player defeated?
        - Player chose to end?
        """
        # return session.fights_completed >= MAX_FIGHTS
        pass
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send message to specific client via connection manager"""
        if self.connection_manager:
            await self.connection_manager.send_message(client_id, message)
        else:
            logger.error(f"No connection manager available to send message to {client_id}")