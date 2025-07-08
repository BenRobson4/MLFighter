import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from ..game_loop import GameEngine, GameState
from ..players import Player
from ..replays import ReplayRecorder
from ..globals import FightStatus
from ..globals.constants import ARENA_WIDTH, ARENA_HEIGHT, MAX_FRAMES
from ..data_classes import FightContext

logger = logging.getLogger(__name__)

class GameManager:
    """
    Manages multiple concurrent fights between players.
    Handles game engine lifecycle, fight execution, and result tracking.
    """
    
    def __init__(self, 
                 arena_width: int = ARENA_WIDTH,
                 arena_height: int = ARENA_HEIGHT):
        """
        Initialize the GameManager with default fight parameters.
        
        Args:
            arena_width: Width of the fighting arena
            arena_height: Height of the fighting arena
            max_frames_per_fight: Maximum frames before timeout (3600 = 60 seconds at 60 FPS)
        """
        # Fight configuration
        self.arena_width = arena_width
        self.arena_height = arena_height
        
        # Active fights tracking
        self.active_fights: Dict[str, FightContext] = {}  # fight_id -> FightContext
        self.client_to_fight: Dict[str, str] = {}  # client_id -> fight_id
        
        # Completed fights history (limited size to prevent memory issues)
        self.completed_fights: Dict[str, FightContext] = {}
        self.max_completed_history = 100
        
        # Fight ID counter for unique identification
        self._fight_counter = 0
        
        logger.info(f"GameManager initialized with arena {arena_width}x{arena_height}")
    
    # ==================== FIGHT LIFECYCLE MANAGEMENT ====================
    
    def create_fight(self, 
                     client_1_id: str, 
                     client_2_id: str,
                     player_1: Player,
                     player_2: Player) -> str:
        """
        Create a new fight between two players.
        
        Args:
            client_1_id: ID of first client
            client_2_id: ID of second client
            player_1: First player's Player object
            player_2: Second player's Player object
            
        Returns:
            fight_id: Unique identifier for this fight
            
        Raises:
            ValueError: If either client is already in a fight
        """
        # ==================== VALIDATION ====================
        # Check if either client is already in a fight
        if client_1_id in self.client_to_fight:
            existing_fight_id = self.client_to_fight[client_1_id]
            if existing_fight_id in self.active_fights:
                raise ValueError(f"Client {client_1_id} is already in fight {existing_fight_id}")
                
        if client_2_id in self.client_to_fight:
            existing_fight_id = self.client_to_fight[client_2_id]
            if existing_fight_id in self.active_fights:
                raise ValueError(f"Client {client_2_id} is already in fight {existing_fight_id}")
        
        # ==================== FIGHT ID GENERATION ====================
        # Generate unique fight ID
        self._fight_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fight_id = f"fight_{timestamp}_{self._fight_counter}"
        
        # ==================== GAME STATE INITIALIZATION ====================
        # Create fresh game state for this fight
        game_state = GameState(
            arena_width=self.arena_width,
            arena_height=self.arena_height
        )

        # ==================== GAME ENGINE SETUP ====================
        # Create new game engine instance for this fight
        game_engine = GameEngine()

        # Set up players in the engine
        game_engine.set_player(1, player_1)
        game_engine.set_player(2, player_2)

        # IMPORTANT: Set player states in the GameState
        game_state.set_player_state(1, player_1.state)
        game_state.set_player_state(2, player_2.state)

        # Set the game state
        game_engine.set_state(game_state)

        # Reset engine to ensure clean state
        game_engine.reset()
        
        # ==================== FIGHT CONTEXT CREATION ====================
        # Create fight context to track all fight data
        fight_context = FightContext(
            fight_id=fight_id,
            client_1_id=client_1_id,
            client_2_id=client_2_id,
            player_1=player_1,
            player_2=player_2,
            game_engine=game_engine,
            game_state=game_state,
            status=FightStatus.INITIALIZING,
            start_time=None,
            end_time=None,
            winner=None,
            total_frames=0,
            replay_data=None
        )
        
        # ==================== REGISTRATION ====================
        # Register the fight in tracking dictionaries
        self.active_fights[fight_id] = fight_context
        self.client_to_fight[client_1_id] = fight_id
        self.client_to_fight[client_2_id] = fight_id
        
        logger.info(f"Created fight {fight_id}: {client_1_id} vs {client_2_id}")
        
        return fight_id
    
    # ==================== FIGHT EXECUTION ====================
    
    async def run_fight(self, fight_id: str) -> FightContext:
        """
        Execute a fight to completion.
        
        Args:
            fight_id: ID of the fight to run
            
        Returns:
            FightContext with completed fight data
            
        Raises:
            KeyError: If fight_id doesn't exist
            RuntimeError: If fight encounters an error
        """
        # ==================== VALIDATION ====================
        if fight_id not in self.active_fights:
            raise KeyError(f"Fight {fight_id} not found")
            
        fight_context = self.active_fights[fight_id]
        
        if fight_context.status != FightStatus.INITIALIZING:
            raise RuntimeError(f"Fight {fight_id} is not in INITIALIZING state (current: {fight_context.status})")
        
        # ==================== FIGHT INITIALIZATION ====================
        logger.info(f"Starting fight {fight_id}")
        
        fight_context.status = FightStatus.IN_PROGRESS
        fight_context.start_time = datetime.now()
        
        game_engine = fight_context.game_engine
        game_state = fight_context.game_state
        
        # ==================== MAIN FIGHT LOOP ====================
        try:
            frame_count = 0
            
            while not game_engine.fight_over:
                # ========== FRAME PROCESSING ==========
                # Step the game engine forward one frame
                game_state = game_engine.step(game_state)
                frame_count += 1
                fight_context.total_frames = frame_count
                
                # ========== ASYNC YIELD ==========
                # Yield control periodically to prevent blocking other fights
                if frame_count % 10 == 0:  # Every 10 frames
                    await asyncio.sleep(0)
            
            # ==================== FIGHT COMPLETION ====================
            # Mark fight as completed
            fight_context.status = FightStatus.COMPLETED
            fight_context.end_time = datetime.now()
            fight_context.winner = game_engine.winner
            
            # ==================== REPLAY EXTRACTION ====================
            # Extract replay data from the recorder
            if game_engine.replay_recorder:
                fight_context.replay_data = {
                    "metadata": game_engine.replay_recorder.metadata,
                    "frames": game_engine.replay_recorder.frames,
                    "winner": game_engine.winner,
                    "total_frames": frame_count
                }
                
                # Save replay to file
                replay_filepath = game_engine.replay_recorder.save_replay(game_engine.winner)
                logger.info(f"Fight {fight_id} replay saved to {replay_filepath}")

                # Clear the recorder after extracting data
                game_engine.replay_recorder = None
            
            # ==================== STATISTICS UPDATE ====================
            # Log fight completion statistics
            duration = (fight_context.end_time - fight_context.start_time).total_seconds()
            logger.info(f"Fight {fight_id} completed: "
                       f"Winner=Player{fight_context.winner}, "
                       f"Frames={frame_count}, "
                       f"Duration={duration:.2f}s")
            
            # ==================== CLEANUP ====================
            # Move fight to completed history
            self._archive_fight(fight_id)
            
            return fight_context
            
        except Exception as e:
            # ==================== ERROR HANDLING ====================
            logger.error(f"Error during fight {fight_id}: {e}")
            
            fight_context.status = FightStatus.ERROR
            fight_context.end_time = datetime.now()
            fight_context.error_message = str(e)
            
            # Still try to save partial replay if available
            if game_engine.replay_recorder and game_engine.replay_recorder.frames:
                try:
                    game_engine.replay_recorder.save_replay(0)  # 0 = no winner due to error
                except Exception as replay_error:
                    logger.error(f"Failed to save error replay: {replay_error}")
            
            # Archive the failed fight
            self._archive_fight(fight_id)
            
            raise RuntimeError(f"Fight {fight_id} failed: {e}") from e
    
    async def run_fight_batch(self, 
                            client_1_id: str, 
                            client_2_id: str,
                            player_1: Player,
                            player_2: Player,
                            num_fights: int = 50,
                            record_interval: int = 10) -> Dict[str, Any]:
        """Run a batch of fights between the same players, recording only at intervals"""
        batch_results = {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_fights": num_fights,
            "completed_fights": 0,
            "client_1_wins": 0,
            "client_2_wins": 0,
            "recorded_fight_ids": [],
            "recorded_replays": [],
            "start_time": datetime.now(),
            "end_time": None,
            "total_frames": 0
        }
        
        for fight_num in range(1, num_fights + 1):
            # Determine if this fight should be recorded
            should_record = (fight_num % record_interval == 0)
            
            fight_id = self.create_fight(client_1_id, client_2_id, player_1, player_2)

            # Debug: Check recording status
            fight_context = self.active_fights[fight_id]
            logger.debug(f"Fight {fight_num}: recording={fight_context.game_engine.is_recording}")

            # Set recording flag
            if should_record:
                self.active_fights[fight_id].game_engine.set_recording(True)
                logger.info(f"Enabled recording for fight {fight_num}")
            else:
                self.active_fights[fight_id].game_engine.set_recording(False)
            
            # Run fight
            completed_context = await self.run_fight(fight_id)
            
            # Update batch statistics
            batch_results["completed_fights"] += 1
            batch_results["total_frames"] += completed_context.total_frames
            
            if completed_context.winner == 1:
                batch_results["client_1_wins"] += 1
            elif completed_context.winner == 2:
                batch_results["client_2_wins"] += 1
            
            # Store replay data for recorded fights
            if should_record:
                logger.info(f"Fight {fight_num} should be recorded")
                if completed_context.replay_data:
                    logger.info(f"Fight {fight_num} has replay data with {len(completed_context.replay_data.get('frames', []))} frames")
                    batch_results["recorded_fight_ids"].append(fight_id)
                    batch_results["recorded_replays"].append(completed_context.replay_data)
                else:
                    logger.warning(f"Fight {fight_num} was marked for recording but has no replay data")
                    
            # Reset player state for next fight
            player_1.state.health = player_1.state.max_health
            player_2.state.health = player_2.state.max_health
            
            # Yield control to allow other tasks to run
            await asyncio.sleep(0)
        
        batch_results["end_time"] = datetime.now()
        duration = (batch_results["end_time"] - batch_results["start_time"]).total_seconds()
        logger.info(f"Batch completed: {num_fights} fights in {duration:.2f}s, "
                f"Client 1 wins: {batch_results['client_1_wins']}, "
                f"Client 2 wins: {batch_results['client_2_wins']}")
        
        return batch_results
    
    # ==================== FIGHT CANCELLATION ====================
    
    def cancel_fight(self, fight_id: str, reason: str = "Unknown") -> bool:
        """
        Cancel an active fight.
        
        Args:
            fight_id: ID of the fight to cancel
            reason: Reason for cancellation
            
        Returns:
            True if fight was cancelled, False if fight wasn't active
        """
        if fight_id not in self.active_fights:
            return False
            
        fight_context = self.active_fights[fight_id]
        
        # ==================== CANCELLATION LOGIC ====================
        if fight_context.status == FightStatus.IN_PROGRESS:
            logger.warning(f"Cancelling in-progress fight {fight_id}: {reason}")
            
            fight_context.status = FightStatus.CANCELLED
            fight_context.end_time = datetime.now()
            fight_context.error_message = f"Cancelled: {reason}"
            
            # Try to save partial replay
            if fight_context.game_engine.replay_recorder:
                try:
                    fight_context.game_engine.replay_recorder.save_replay(0)
                except Exception as e:
                    logger.error(f"Failed to save cancelled fight replay: {e}")
            
            # Archive the cancelled fight
            self._archive_fight(fight_id)
            
            return True
        
        return False
    
    # ==================== FIGHT QUERIES ====================
    
    def get_fight_status(self, fight_id: str) -> Optional[FightStatus]:
        """
        Get the current status of a fight.
        
        Args:
            fight_id: ID of the fight
            
        Returns:
            FightStatus or None if fight doesn't exist
        """
        if fight_id in self.active_fights:
            return self.active_fights[fight_id].status
        elif fight_id in self.completed_fights:
            return self.completed_fights[fight_id].status
        return None
    
    def get_fight_context(self, fight_id: str) -> Optional[FightContext]:
        """
        Get the full context for a fight.
        
        Args:
            fight_id: ID of the fight
            
        Returns:
            FightContext or None if fight doesn't exist
        """
        if fight_id in self.active_fights:
            return self.active_fights[fight_id]
        elif fight_id in self.completed_fights:
            return self.completed_fights[fight_id]
        return None
    
    def get_client_fight(self, client_id: str) -> Optional[str]:
        """
        Get the fight ID for a client's current fight.
        
        Args:
            client_id: ID of the client
            
        Returns:
            fight_id or None if client isn't in a fight
        """
        return self.client_to_fight.get(client_id)
    
    def is_client_in_fight(self, client_id: str) -> bool:
        """
        Check if a client is currently in an active fight.
        
        Args:
            client_id: ID of the client
            
        Returns:
            True if client is in an active fight
        """
        fight_id = self.client_to_fight.get(client_id)
        return fight_id is not None and fight_id in self.active_fights
    
    # ==================== INTERNAL HELPERS ====================
    
    def _archive_fight(self, fight_id: str):
        """
        Move a fight from active to completed history.
        
        Args:
            fight_id: ID of the fight to archive
        """
        if fight_id not in self.active_fights:
            return
            
        fight_context = self.active_fights[fight_id]
        
        # ==================== CLEANUP REFERENCES ====================
        # Remove client -> fight mappings
        if fight_context.client_1_id in self.client_to_fight:
            del self.client_to_fight[fight_context.client_1_id]
        if fight_context.client_2_id in self.client_to_fight:
            del self.client_to_fight[fight_context.client_2_id]
        
        # ==================== ARCHIVE FIGHT ====================
        # Move to completed fights
        self.completed_fights[fight_id] = fight_context
        del self.active_fights[fight_id]
        
        # ==================== HISTORY MANAGEMENT ====================
        # Limit completed history size
        if len(self.completed_fights) > self.max_completed_history:
            # Remove oldest completed fights
            sorted_fights = sorted(
                self.completed_fights.items(),
                key=lambda x: x[1].end_time or datetime.min
            )
            
            # Remove oldest fights
            num_to_remove = len(self.completed_fights) - self.max_completed_history
            for fight_id_to_remove, _ in sorted_fights[:num_to_remove]:
                del self.completed_fights[fight_id_to_remove]
                logger.debug(f"Removed old fight {fight_id_to_remove} from history")
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics about managed fights.
        
        Returns: 
            Dictionary with fight statistics
        """
        active_count = len(self.active_fights)
        completed_count = len(self.completed_fights)
        
        # Count by status
        status_counts = {}
        for fight in self.active_fights.values():
            status_counts[fight.status.value] = status_counts.get(fight.status.value, 0) + 1
        
        return {
            "active_fights": active_count,
            "completed_fights": completed_count,
            "total_fights_created": self._fight_counter,
            "status_breakdown": status_counts,
            "clients_in_fights": len(self.client_to_fight)
        }