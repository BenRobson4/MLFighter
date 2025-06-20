import os
from typing import List, Dict, Any, Optional
import tkinter.messagebox as messagebox

from ..agents import AdaptiveDQNAgent, AdaptiveConfig
from ..framework import FightingGameFramework
from ..config.config_manager import ConfigManager
from ..ui.option_selector import OptionGenerator, OptionSelectorUI, AgentOption
from ..ui.multi_replay_player import MultiReplayPlayer


class GameManager:
    """Manages the iterative training game format with token system"""
    
    def __init__(self, rounds_per_phase: int = 250, replays_to_show: int = 5):
        self.rounds_per_phase = rounds_per_phase
        self.replays_to_show = replays_to_show
        
        # Configuration manager
        self.config_manager = ConfigManager()
        self.option_generator = OptionGenerator(self.config_manager)
        
        # Create agents
        self.agent1 = None
        self.agent2 = None
        
        # Store current configurations
        self.agent1_config = None
        self.agent2_config = None
        
        # Model save paths
        self.agent1_save_path = None
        self.agent2_save_path = None
        
        # Training stats
        self.phase_number = 0
        self.total_episodes = 0
        self.phase_history = []
        self.player_stats = {
            'player1': {'wins': 0, 'total_games': 0, 'last_win_rate': 0.5},
            'player2': {'wins': 0, 'total_games': 0, 'last_win_rate': 0.5}
        }
        
        # Directories
        os.makedirs("models", exist_ok=True)
        os.makedirs("replays", exist_ok=True)
    
    def calculate_player_tokens(self, player_id: str) -> int:
        """Calculate available tokens for a player based on their stats"""
        player_stats = self.player_stats[player_id]
        tokens = 5
        return tokens
    
    def configure_agent(self, player_name: str, player_id: str, 
                       current_config: Optional[AgentOption] = None) -> Optional[AgentOption]:
        """Show configuration UI for an agent"""
        first_round = (self.phase_number == 0)
        
        if first_round:
            # Generate random options for first round
            options = self.option_generator.generate_options(
                self.config_manager.config["initial_options"]["num_options"]
            )
        else:
            # No random options after first round
            options = []
        
        # Calculate tokens
        tokens = self.calculate_player_tokens(player_id)
        
        # Show UI
        selected_config = None
        
        def on_complete(config: AgentOption):
            nonlocal selected_config
            selected_config = config
        
        ui = OptionSelectorUI(
            player_name, 
            options, 
            tokens,
            self.config_manager,
            on_complete,
            current_config=current_config,
            first_round=first_round
        )
        ui.show()
        
        return selected_config
    
    def create_or_update_agent(self, agent: Optional[AdaptiveDQNAgent], 
                              config: AgentOption, player_id: str,
                              save_path: Optional[str] = None) -> AdaptiveDQNAgent:
        """Create new agent or update existing one"""
        if agent is None and save_path and os.path.exists(save_path):
            # Load existing agent from file
            print(f"Loading {player_id} from {save_path}")
            agent = AdaptiveDQNAgent.load_from_file(save_path, player_id)
            
            # Update with new configuration changes (features, learning params)
            # but keep the current epsilon from training
            current_epsilon = agent.epsilon
            agent.update_configuration(
                features=config.features,
                epsilon=current_epsilon,  # Keep current epsilon
                epsilon_decay=config.decay,
                learning_rate=config.learning_rate
            )
        elif agent is None:
            # Create new agent (first round)
            adaptive_config = AdaptiveConfig()
            agent = AdaptiveDQNAgent(adaptive_config, player_id)
            agent.update_configuration(
                fighter=config.fighter,
                features=config.features,
                epsilon=config.epsilon,
                epsilon_decay=config.decay,
                learning_rate=config.learning_rate
            )
        else:
            # Update existing agent
            agent.update_configuration(
                fighter=config.fighter,
                features=config.features,
                epsilon=agent.epsilon,  # Keep current epsilon
                epsilon_decay=config.decay,
                learning_rate=config.learning_rate
            )
        
        return agent
    
    def run_training_phase(self) -> List[str]:
        """Run one phase of training"""
        print(f"\n=== Phase {self.phase_number + 1} - Training {self.rounds_per_phase} episodes ===")
        print(f"Player 1 starting epsilon: {self.agent1.epsilon:.3f}")
        print(f"Player 2 starting epsilon: {self.agent2.epsilon:.3f}")
        
        # Extract fighter names from agent configs
        player1_fighter = self.agent1.config.fighter if self.agent1.config else 'Default'
        player2_fighter = self.agent2.config.fighter if self.agent2.config else 'Default'

        framework = FightingGameFramework(self.agent1, self.agent2, record_replays=True,
                                          player1_fighter=player1_fighter, player2_fighter=player2_fighter)
        phase_results = []
        replay_files = []
        
        for episode in range(self.rounds_per_phase):
            # Record last N episodes
            should_record = episode >= (self.rounds_per_phase - self.replays_to_show)
            
            result = framework.run_episode(record=should_record)
            phase_results.append(result)
            
            if should_record and result.get('replay_file'):
                replay_files.append(result['replay_file'])
            
            # Update stats
            winner = result['winner']
            self.player_stats[winner]['wins'] += 1
            self.player_stats['player1']['total_games'] += 1
            self.player_stats['player2']['total_games'] += 1
            
            # Progress update
            if episode % 50 == 0:
                recent = phase_results[-50:] if len(phase_results) >= 50 else phase_results
                p1_wins = sum(1 for r in recent if r['winner'] == 'player1')
                win_rate = p1_wins / len(recent)
                print(f"Episode {episode}/{self.rounds_per_phase}: "
                      f"P1 Win Rate: {win_rate:.2%}, "
                      f"P1 ε: {self.agent1.epsilon:.3f}, "
                      f"P2 ε: {self.agent2.epsilon:.3f}")
            
            self.total_episodes += 1
        
        # Calculate phase win rates
        p1_phase_wins = sum(1 for r in phase_results if r['winner'] == 'player1')
        self.player_stats['player1']['last_win_rate'] = p1_phase_wins / len(phase_results)
        self.player_stats['player2']['last_win_rate'] = 1 - self.player_stats['player1']['last_win_rate']
        
        # Save models with current state
        self.agent1_save_path = f"fighting_game/models/agent1_phase{self.phase_number}_ep{self.total_episodes}.pth"
        self.agent2_save_path = f"fighting_game/models/agent2_phase{self.phase_number}_ep{self.total_episodes}.pth"
        self.agent1.save(self.agent1_save_path)
        self.agent2.save(self.agent2_save_path)
        print(f"Models saved: {self.agent1_save_path}, {self.agent2_save_path}")
        
        print(f"Player 1 ending epsilon: {self.agent1.epsilon:.3f}")
        print(f"Player 2 ending epsilon: {self.agent2.epsilon:.3f}")
        
        # Store current configurations
        self.agent1_config = self.agent1.get_current_config()
        self.agent2_config = self.agent2.get_current_config()
        
        # Store phase history
        self.phase_history.append({
            'phase': self.phase_number,
            'total_episodes': self.total_episodes,
            'p1_win_rate': self.player_stats['player1']['last_win_rate'],
            'p1_epsilon_start': phase_results[0] if phase_results else 0,
            'p1_epsilon_end': self.agent1.epsilon,
            'p2_epsilon_end': self.agent2.epsilon,
            'p1_config': self.agent1_config.to_dict(),
            'p2_config': self.agent2_config.to_dict()
        })
        
        return replay_files
    
    def show_replays(self, replay_files: List[str]):
        """Show multiple replays in sequence"""
        if not replay_files:
            print("No replays to show")
            return
        
        print(f"\nShowing {len(replay_files)} replays...")
        player = MultiReplayPlayer(replay_files)
        player.play_all()

    def show_statistics(self):
        """Display training statistics"""
        print("\n=== Phase Statistics ===")
        print(f"Phase {self.phase_number} Complete")
        print(f"Total Episodes: {self.total_episodes}")
        
        # Win rates
        p1_total_wr = (self.player_stats['player1']['wins'] / 
                      self.player_stats['player1']['total_games'] 
                      if self.player_stats['player1']['total_games'] > 0 else 0)
        
        print(f"\nOverall Win Rates:")
        print(f"  Player 1: {p1_total_wr:.2%} ({self.player_stats['player1']['wins']} wins)")
        print(f"  Player 2: {1-p1_total_wr:.2%} ({self.player_stats['player2']['wins']} wins)")
        
        print(f"\nLast Phase Win Rates:")
        print(f"  Player 1: {self.player_stats['player1']['last_win_rate']:.2%}")
        print(f"  Player 2: {self.player_stats['player2']['last_win_rate']:.2%}")
        
        # Current epsilon values (after decay)
        if self.agent1 and self.agent2:
            print(f"\nCurrent Epsilon Values (after decay):")
            print(f"  Player 1: {self.agent1.epsilon:.4f}")
            print(f"  Player 2: {self.agent2.epsilon:.4f}")
        
        # Token calculation for next round
        print(f"\nTokens for Next Phase:")
        print(f"  Player 1: {self.calculate_player_tokens('player1')} tokens")
        print(f"  Player 2: {self.calculate_player_tokens('player2')} tokens")
        print("\n=== End of Phase Statistics ===")
    
    def run_game(self):
        """Main game loop"""
        print("=== Fighting Game Training System ===")
        print(f"Configuration: {self.rounds_per_phase} rounds per phase")
        print(f"Token System: Enabled")
        print(f"Showing last {self.replays_to_show} fights after each phase\n")
        
        try:
            while True:
                # Configure agents
                print(f"\n=== Phase {self.phase_number + 1} Configuration ===")
                
                # Player 1 configuration
                print(f"\nPlayer 1 Tokens: {self.calculate_player_tokens('player1')}")
                if self.phase_number > 0:
                    print(f"Current epsilon (after decay): {self.agent1_config.epsilon:.3f}")
                    print(f"Current features: {', '.join(sorted(self.agent1_config.features))}")
                
                p1_config = self.configure_agent(
                    "Player 1", 
                    "player1",
                    current_config=self.agent1_config if self.phase_number > 0 else None
                )

                if p1_config is None:
                    print("Player 1 configuration cancelled. Exiting.")
                    break
                
                self.agent1 = self.create_or_update_agent(
                    self.agent1, 
                    p1_config, 
                    "player1",
                    save_path=self.agent1_save_path
                )
                print(f"Player 1 configured with {len(p1_config.features)} features and fighter {self.agent1.config.fighter}")
                
                # Player 2 configuration
                print(f"\nPlayer 2 Tokens: {self.calculate_player_tokens('player2')}")
                if self.phase_number > 0:
                    print(f"Current epsilon (after decay): {self.agent2_config.epsilon:.3f}")
                    print(f"Current features: {', '.join(sorted(self.agent2_config.features))}")
                
                p2_config = self.configure_agent(
                    "Player 2", 
                    "player2",
                    current_config=self.agent2_config if self.phase_number > 0 else None
                )
                if p2_config is None:
                    print("Player 2 configuration cancelled. Exiting.")
                    break
                
                self.agent2 = self.create_or_update_agent(
                    self.agent2, 
                    p2_config, 
                    "player2",
                    save_path=self.agent2_save_path
                )
                print(f"Player 2 configured with {len(p2_config.features)} features and fighter {self.agent2.config.fighter}")
                
                # Run training
                replay_files = self.run_training_phase()
                
                # Show statistics
                self.show_statistics()
                
                # Show replays
                self.show_replays(replay_files)
                
                # Increment phase
                self.phase_number += 1
                
                # Ask to continue
                print("\nPress Enter to continue to next phase, or 'q' to quit: ", end='')
                if input().lower() == 'q':
                    break
        
        except KeyboardInterrupt:
            print("\n\nTraining interrupted by user.")
        
        print("\n=== Training Complete ===")
        self.show_statistics()