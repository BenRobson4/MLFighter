import time

from .game_engine import GameEngine, GameState
from ..players import Player, PlayerStateBuilder
from ..shop import ShopManager
from ..server import ConnectionManager
from ..globals.constants import ARENA_WIDTH, ARENA_HEIGHT, GROUND_LEVEL, SPAWN_MARGIN
from ..globals import State

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GameManager:

    def __init__(self):
        """
        Initialize the game manager with necessary components.
        This includes setting up the game state, player connections, and initial configurations.
        """
        self.game_state = None  # Placeholder for the game state object
        self.game_finished = False

        self.shop_manager = ShopManager
        self.connection_manager = ConnectionManager
        self.engine = GameEngine()

        self.player1 = None  
        self.player2 = None  
        # Attributes for fighter selection
        self.player1_options = None  
        self.player2_options = None  
        self.player1_choice = None 
        self.player2_choice = None  

        self.ground_level = GROUND_LEVEL
        self.spawn_margin = SPAWN_MARGIN  # Margin from edges for player spawn positions


    def play_game(self):

        # Network system for online play
        self._connect_players()

        # Initilisation steps before main game cycle
        self._create_initial_shop()

        self._initialise_players()

        while not self.game_finished:

            self._run_fights()

            self._send_replays()

            self._shop_phase()

            self._update_players()

        self._send_end_info()

    def _connect_players(self):
        """
        Connect players to the game server or matchmaking system.
        This could involve network setup, player authentication, etc.
        """
        pass

    def _create_initial_shop(self):

        for player in self.players:
            # Create an initial shop for each player
            shop = self.shop_manager.create_initial_shop(player)
            self.connection_manager.send_shop_update(player, shop)

    def _initialise_players(self) -> None:
        """
        Initialize or reset players for a new game session.
        This handles both fresh initialization and match-to-match resets.
        """
        
        # ========== 1. PLAYER CREATION / LOADING ==========
        if not hasattr(self, 'player1') or self.player1 is None:
            # First time initialization - create players from already-made choices
            logger.info("First match - creating new players from selections")
            
            if not hasattr(self, 'player1_choice') or not hasattr(self, 'player2_choice'):
                raise RuntimeError("Player choices not found. Run _send_options() first.")
            
            if not hasattr(self, 'player1_options') or not hasattr(self, 'player2_options'):
                raise RuntimeError("Player options not found. Run _generate_options() first.")
            
            # Validate choice indices
            if self.player1_choice not in range(len(self.player1_options)):
                raise ValueError(f"Invalid player 1 choice: {self.player1_choice}")
            if self.player2_choice not in range(len(self.player2_options)):
                raise ValueError(f"Invalid player 2 choice: {self.player2_choice}")
            
            # Get selected configurations
            p1_config = self.player1_options[self.player1_choice]
            p2_config = self.player2_options[self.player2_choice]
            
            # Create Player 1
            self.player1 = Player(
                player_id="player1",
                fighter_name=p1_config['fighter_name'],
                starting_gold=p1_config.get('starting_gold', 1000),
                starting_level=p1_config.get('starting_level', 1),
                learning_parameters=p1_config['learning_parameters'],
                items=p1_config.get('starting_items', None),
                num_actions=6,
                num_features=20
            )
            
            # Create Player 2
            self.player2 = Player(
                player_id="player2",
                fighter_name=p2_config['fighter_name'],
                starting_gold=p2_config.get('starting_gold', 1000),
                starting_level=p2_config.get('starting_level', 1),
                learning_parameters=p2_config['learning_parameters'],
                items=p2_config.get('starting_items', None),
                num_actions=6,
                num_features=20
            )
            
            logger.info(f"Created Player 1: {p1_config['fighter_name']} (choice {self.player1_choice + 1}/{len(self.player1_options)})")
            logger.info(f"Created Player 2: {p2_config['fighter_name']} (choice {self.player2_choice + 1}/{len(self.player2_options)})")
            
            # Clean up - options and choices no longer needed
            del self.player1_options
            del self.player2_options
            del self.player1_choice
            del self.player2_choice
            
        else:
            # Players already exist - prepare for rematch
            logger.info("Preparing existing players for the next fight")
            
            # Log current player progress
            logger.debug(f"Player 1 ({self.player1.fighter.name}): "
                        f"Matches: {self.player1.matches_played}, "
                        f"Wins: {self.player1.wins}, "
                        f"Gold: {self.player1.gold}, "
                        f"Epsilon: {self.player1.learning_parameters.epsilon:.4f}")
            logger.debug(f"Player 2 ({self.player2.fighter.name}): "
                        f"Matches: {self.player2.matches_played}, "
                        f"Wins: {self.player2.wins}, "
                        f"Gold: {self.player2.gold}, "
                        f"Epsilon: {self.player2.learning_parameters.epsilon:.4f}")
        
        
        # ========== 2. GENERATE PLAYER STATES ==========
        # Create fresh PlayerState objects for the match

        # Calculate spawn positions
        player1_spawn_x = self.spawn_margin
        player2_spawn_x = ARENA_WIDTH - self.spawn_margin
        spawn_y = self.ground_level
        
        # Update PlayerState objects' spawn_x and spawn_y parameters
        self.player1.state.start_x = player1_spawn_x
        self.player1.state.start_y = spawn_y

        self.player2.state.start_x = player2_spawn_x
        self.player2.state.start_y = spawn_y
        
        # Verify critical state resets
        assert self.player1.state.health == self.player1.state.max_health, "Player 1 health not reset"
        assert self.player2.state.health == self.player2.state.max_health, "Player 2 health not reset"
        assert self.player1.state_machine.current_state == State.IDLE, "Player 1 state not reset"
        assert self.player2.state_machine.current_state == State.IDLE, "Player 2 state not reset"
        assert self.player1.state.x == player1_spawn_x, "Player 1 X position not reset"
        assert self.player2.state.x == player2_spawn_x, "Player 2 X position not reset"
        
        logger.info("Player states initialized successfully")
        
        # ========== 3. SYNCHRONIZE WITH GAME ENGINE ==========
        # Ensure game engine has current player states
        
        # Register players with game engine
        self.engine.set_player(1, self.player1)
        self.engine.set_player(2, self.player2)
    
        logger.info(f"Players initialized: {self.player1.player_id} vs {self.player2.player_id}")
        logger.debug(f"P1 State: HP={self.player1.state.health}, Pos=({self.player1.state.x}, {self.player1.state.y})")
        logger.debug(f"P2 State: HP={self.player2.state.health}, Pos=({self.player2.state.x}, {self.player2.state.y})")

        # ========== 4. INITIALIZE GAME STATE ==========
        # Create the game state object from the initial player states
        self.game_state = GameState(
            arena_width=ARENA_WIDTH,
            arena_height=ARENA_HEIGHT,
            player1_state=self.player1_state,
            player2_state=self.player2.state
        )
        self.engine.set_state(self.game_state)

    def _run_fights(self, num_fights: int) -> None:
        """
        Run multiple fights between the players.
        
        Args:
            num_fights: Total number of fights to run
        """
        logger.info(f"Starting {num_fights} fight(s) between {self.player1.player_id} and {self.player2.player_id}")
        
        # Calculate recording interval (record every 20% of fights)
        recording_interval = max(1, num_fights // 5)
        
        # Track fight results
        fight_results = []
        
        for fight_num in range(1, num_fights + 1):
            logger.info(f"=== Starting Fight {fight_num}/{num_fights} ===")
            
            # Initialize players for this fight
            self._initialise_players()

            frames_elapsed = 0
            fight_start = time.time()
            
            # Determine if we should record this fight
            should_record = (fight_num % 10 == 0) or (fight_num == num_fights)
            self.engine.is_recording = should_record
            
            if should_record:
                logger.info(f"Recording enabled for fight {fight_num}")
            
            # Run the fight until completion
            while not self.engine.fight_over:
                # Step the game engine
                frames_elapsed += 1
                self.game_state = self.engine.step(game_state=self.game_state)

            fight_end = time.time()
            fight_duration = fight_end - fight_start

            # Determine winner and update player statistics
            if self.engine.winner is not 0:
                winner_id = self.engine.winner
                if winner_id == 1:
                    self.player1.end_match(won=True, total_reward=self.player1.state.total_reward)
                    self.player2.end_match(won=False, total_reward=self.player2.state.total_reward)
                    winner_name = self.player1.player_id
                else:
                    self.player1.end_match(won=False, total_reward=self.player1_state.total_reward)
                    self.player2.end_match(won=True, total_reward=self.player2.state.total_reward)
                    winner_name = self.player2.player_id
                    
                logger.info(f"Fight {fight_num} completed: {winner_name} wins! \n Frames: {frames_elapsed}, "
                            f"Duration: {fight_duration:.2f}s, "
                            f"P1 Health: {self.player1.state.health}, P2 Health: {self.player2.state.health}")
            else:
                # Draw or timeout
                self.player1.end_match(won=False, total_reward=self.player1.state.total_reward)
                self.player2.end_match(won=False, total_reward=self.player2.state.total_reward)
                logger.info(f"Fight {fight_num} ended in a draw.")
            
            # Store fight results
            fight_results.append({
                'fight_number': fight_num,
                'winner': self.engine.winner,
                'duration': fight_duration,
                'frames': frames_elapsed,
                'p1_health': self.player1.state.health,
                'p2_health': self.player2.state.health,
                'p1_reward': self.player1.state.accumulated_reward,
                'p2_reward': self.player2.state.accumulated_reward,
                'recorded': should_record
            })
            
            # Reset game engine for next fight
            self.engine.reset()
            
            # Log progress periodically
            if fight_num % 1 == 0 or fight_num == num_fights:
                p1_win_rate = self.player1.wins / max(1, self.player1.matches_played)
                p2_win_rate = self.player2.wins / max(2, self.player2.matches_played)
                logger.info(f"Progress: {fight_num}/{num_fights} fights complete. "
                        f"Win rates - P1: {p1_win_rate:.2%}, P2: {p2_win_rate:.2%}")
        
        # Final summary
        logger.info(f"=== All {num_fights} fights completed ===")
        logger.info(f"Player 1 ({self.player1.fighter.name}): {self.player1.wins} wins, "
                f"{self.player1.losses} losses")
        logger.info(f"Player 2 ({self.player2.fighter.name}): {self.player2.wins} wins, "
                f"{self.player2.losses} losses")
        
        # Store results
        self.fight_history = fight_results