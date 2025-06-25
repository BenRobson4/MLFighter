import logging
import time
from pathlib import Path
import sys

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent))

from .players.player import Player
from .data_classes import LearningParameters
from .game_loop.game_engine import GameEngine
from .game_loop.game_manager import GameManager
from .globals import Action, State


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training_run.log')
    ]
)

logger = logging.getLogger("main")


class TrainingRunner:
    """Main class to run training fights between AI players"""
    
    def __init__(self):
        self.game_config = {
            'stage_width': 800,
            'stage_height': 600,
            'ground_level': 100,
            'max_frames_per_fight': 3600,  # 60 seconds at 60 FPS
            'headless': True,              # No GUI
        }
        
        # Create game engine
        self.game_engine = GameEngine()
        
        # Create game manager
        self.game_manager = GameManager()
        
        # Create mock players
        self._create_mock_players()
    
    def _create_mock_players(self):
        """Create mock players for testing"""
        # Create player 1 - Aggressive fighter
        p1_params = LearningParameters(
            epsilon=0.9,
            epsilon_decay=0.995,
            epsilon_min=0.05,
            learning_rate=0.0005
        )
        
        self.game_manager.player1 = Player(
            player_id="mock_player1",
            fighter_name="aggressive",
            starting_gold=1000,
            starting_level=1,
            learning_parameters=p1_params,
            num_actions=len(Action),
            num_features=20
        )
        
        # Create player 2 - Defensive fighter
        p2_params = LearningParameters(
            epsilon=0.8,
            epsilon_decay=0.99,
            epsilon_min=0.1,
            learning_rate=0.0003
        )
        
        self.game_manager.player2 = Player(
            player_id="mock_player2",
            fighter_name="defensive",
            starting_gold=1000,
            starting_level=1,
            learning_parameters=p2_params,
            num_actions=len(Action),
            num_features=20
        )
        
        logger.info(f"Created mock players: {self.game_manager.player1.player_id} vs {self.game_manager.player2.player_id}")
        logger.info(f"Player 1: {self.game_manager.player1.fighter.name}")
        logger.info(f"Player 2: {self.game_manager.player2.fighter.name}")
    
    def run_training(self, num_fights: int = 50):
        """Run training fights between players"""
        logger.info(f"Starting training run with {num_fights} fights")
        
        # Initialize game manager
        self.game_manager._initialise_players()
        
        # Start time tracking
        start_time = time.time()
        
        # Run fights
        self.game_manager._run_fights(num_fights)
        
        # Calculate training duration
        duration = time.time() - start_time
        
        # Show results
        self._show_training_results(duration)
        
        # Save player models
        self._save_player_models()
    
    def _show_training_results(self, duration: float):
        """Display training results"""
        p1 = self.game_manager.player1
        p2 = self.game_manager.player2
        
        logger.info("=" * 50)
        logger.info(f"Training completed in {duration:.2f} seconds")
        logger.info(f"Total fights: {p1.matches_played}")
        logger.info(f"Player 1 ({p1.fighter.name}): {p1.wins} wins, {p1.losses} losses, {p1.wins/p1.matches_played:.1%} win rate")
        logger.info(f"Player 2 ({p2.fighter.name}): {p2.wins} wins, {p2.losses} losses, {p2.wins/p2.matches_played:.1%} win rate")
        logger.info(f"Player 1 final epsilon: {p1.learning_parameters.epsilon:.4f}")
        logger.info(f"Player 2 final epsilon: {p2.learning_parameters.epsilon:.4f}")
        logger.info(f"Player 1 total reward: {p1.total_reward:.2f}")
        logger.info(f"Player 2 total reward: {p2.total_reward:.2f}")
        logger.info("=" * 50)
    
    def _save_player_models(self):
        """Save trained player models"""
        models_dir = Path("saved_models")
        models_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save player 1
        p1_path = models_dir / f"player1_{timestamp}.json"
        self.game_manager.player1.save(str(p1_path))
        
        # Save player 2
        p2_path = models_dir / f"player2_{timestamp}.json"
        self.game_manager.player2.save(str(p2_path))
        
        logger.info(f"Player models saved to {models_dir}")


if __name__ == "__main__":
    # Run training
    runner = TrainingRunner()
    runner.run_training(num_fights=50)
    
    logger.info("Training complete!")