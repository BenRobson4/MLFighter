import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
import pygame
from collections import deque
import random
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class Action(Enum):
    LEFT = 0
    RIGHT = 1
    JUMP = 2
    BLOCK = 3
    ATTACK = 4
    IDLE = 5

class GameState:
    """Represents the current state of the fighting game"""
    def __init__(self, arena_width: int = 400, arena_height: int = 600):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.ground_level = arena_height - 100
        
        # Player states
        self.players = {
            'player1': self._create_player_state(200),
            'player2': self._create_player_state(300)
        }
        
        self.game_over = False
        self.winner = None
        self.frame_count = 0
        
    def _create_player_state(self, x_pos: int) -> Dict:
        return {
            'x': x_pos,
            'y': self.ground_level,
            'velocity_x': 0,
            'velocity_y': 0,
            'health': 100,
            'is_jumping': False,
            'is_blocking': False,
            'is_attacking': False,
            'attack_cooldown': 0,
            'facing_right': True
        }
    
    def get_state_vector(self, player_id: str) -> np.ndarray:
        """Convert game state to feature vector for ML model"""
        p1 = self.players['player1']
        p2 = self.players['player2']
        
        # Normalize positions and create relative features
        features = [
            p1['x'] / self.arena_width,
            p1['y'] / self.arena_height,
            p1['health'] / 100,
            p1['velocity_x'] / 10,  # Assuming max velocity ~10
            p1['velocity_y'] / 15,  # Assuming max jump velocity ~15
            int(p1['is_jumping']),
            int(p1['is_blocking']),
            int(p1['is_attacking']),
            p1['attack_cooldown'] / 30,  # Assuming max cooldown ~30 frames
            
            p2['x'] / self.arena_width,
            p2['y'] / self.arena_height,
            p2['health'] / 100,
            p2['velocity_x'] / 10,
            p2['velocity_y'] / 15,
            int(p2['is_jumping']),
            int(p2['is_blocking']),
            int(p2['is_attacking']),
            p2['attack_cooldown'] / 30,
            
            # Distance between players
            abs(p1['x'] - p2['x']) / self.arena_width,
            abs(p1['y'] - p2['y']) / self.arena_height,
        ]
        
        return np.array(features, dtype=np.float32)

class MLAgent(ABC):
    """Abstract base class for ML agents"""
    
    @abstractmethod
    def get_action(self, state: np.ndarray) -> Action:
        """Given game state, return the action to take"""
        pass
    
    @abstractmethod
    def update(self, state: np.ndarray, action: Action, reward: float, 
               next_state: np.ndarray, done: bool):
        """Update the model with experience"""
        pass

class RandomAgent(MLAgent):
    """Simple random agent for testing"""
    
    def get_action(self, state: np.ndarray) -> Action:
        return Action(np.random.randint(0, len(Action)))
    
    def update(self, state: np.ndarray, action: Action, reward: float,
               next_state: np.ndarray, done: bool):
        pass  # Random agent doesn't learn

class GameEngine:
    """Main game engine that handles physics and game logic"""
    
    def __init__(self):
        self.state = GameState()
        self.physics_config = {
            'gravity': 0.8,
            'jump_force': -15,
            'move_speed': 5,
            'attack_range': 80,
            'attack_damage': 10,
            'attack_cooldown': 30
        }
    
    def step(self, player1_action: Action, player2_action: Action) -> Tuple[GameState, Dict[str, float]]:
        """Execute one game step and return new state + rewards"""
        if self.state.game_over:
            return self.state, {'player1': 0, 'player2': 0}
        
        # Store previous health for reward calculation
        prev_health = {
            'player1': self.state.players['player1']['health'],
            'player2': self.state.players['player2']['health']
        }
        
        # Apply actions
        self._apply_action('player1', player1_action)
        self._apply_action('player2', player2_action)
        
        # Update physics
        self._update_physics()
        
        # Handle combat
        self._handle_combat()
        
        # Update cooldowns
        self._update_cooldowns()
        
        # Check win conditions
        self._check_game_over()
        
        # Calculate rewards
        rewards = self._calculate_rewards(prev_health)
        
        self.state.frame_count += 1
        
        return self.state, rewards
    
    def _apply_action(self, player_id: str, action: Action):
        player = self.state.players[player_id]
        
        # Reset action states
        player['is_blocking'] = False
        player['is_attacking'] = False
        
        if action == Action.LEFT:
            player['velocity_x'] = -self.physics_config['move_speed']
            player['facing_right'] = False
        elif action == Action.RIGHT:
            player['velocity_x'] = self.physics_config['move_speed']
            player['facing_right'] = True
        elif action == Action.JUMP and not player['is_jumping']:
            player['velocity_y'] = self.physics_config['jump_force']
            player['is_jumping'] = True
        elif action == Action.BLOCK:
            player['is_blocking'] = True
            player['velocity_x'] = 0
        elif action == Action.ATTACK and player['attack_cooldown'] <= 0:
            player['is_attacking'] = True
            player['attack_cooldown'] = self.physics_config['attack_cooldown']
        else:  # IDLE
            player['velocity_x'] = 0
    
    def _update_physics(self):
        for player in self.state.players.values():
            # Apply gravity
            if player['is_jumping']:
                player['velocity_y'] += self.physics_config['gravity']
            
            # Update positions
            player['x'] += player['velocity_x']
            player['y'] += player['velocity_y']
            
            # Boundary checking
            player['x'] = max(50, min(self.state.arena_width - 50, player['x']))
            
            # Ground collision
            if player['y'] >= self.state.ground_level:
                player['y'] = self.state.ground_level
                player['velocity_y'] = 0
                player['is_jumping'] = False
    
    def _handle_combat(self):
        p1, p2 = self.state.players['player1'], self.state.players['player2']
        distance = abs(p1['x'] - p2['x'])
        
        # Player 1 attacking Player 2
        if (p1['is_attacking'] and distance <= self.physics_config['attack_range'] 
            and not p2['is_blocking']):
            p2['health'] -= self.physics_config['attack_damage']
        
        # Player 2 attacking Player 1
        if (p2['is_attacking'] and distance <= self.physics_config['attack_range'] 
            and not p1['is_blocking']):
            p1['health'] -= self.physics_config['attack_damage']
    
    def _update_cooldowns(self):
        for player in self.state.players.values():
            if player['attack_cooldown'] > 0:
                player['attack_cooldown'] -= 1
    
    def _check_game_over(self):
        p1_health = self.state.players['player1']['health']
        p2_health = self.state.players['player2']['health']
        
        if p1_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player2'
        elif p2_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player1'
        elif self.state.frame_count >= 3600:  # 60 seconds at 60 FPS
            self.state.game_over = True
            self.state.winner = 'player1' if p1_health > p2_health else 'player2'
    
    def _calculate_rewards(self, prev_health: Dict[str, float]) -> Dict[str, float]:
        rewards = {'player1': 0, 'player2': 0}
        
        # Health-based rewards
        p1_health_change = self.state.players['player1']['health'] - prev_health['player1']
        p2_health_change = self.state.players['player2']['health'] - prev_health['player2']
        
        rewards['player1'] += p1_health_change * 0.1 - p2_health_change * 0.1
        rewards['player2'] += p2_health_change * 0.1 - p1_health_change * 0.1
        
        # Win/lose rewards
        if self.state.game_over:
            if self.state.winner == 'player1':
                rewards['player1'] += 100
                rewards['player2'] -= 100
            else:
                rewards['player1'] -= 100
                rewards['player2'] += 100
        
        return rewards
    
    def reset(self) -> GameState:
        """Reset the game to initial state"""
        self.state = GameState()
        return self.state
    
class FightingGameFramework:
    """Main framework class that orchestrates the fighting game"""
    
    def __init__(self, agent1: MLAgent, agent2: MLAgent):
        self.engine = GameEngine()
        self.agents = {'player1': agent1, 'player2': agent2}
        self.game_history = []
    
    def run_episode(self) -> Dict:
        """Run a complete game episode"""
        self.engine.reset()
        episode_data = []
        
        while not self.engine.state.game_over:
            # Get current state
            current_state = {
                'player1': self.engine.state.get_state_vector('player1'),
                'player2': self.engine.state.get_state_vector('player2')
            }
            
            # Get actions from agents
            actions = {
                'player1': self.agents['player1'].get_action(current_state['player1']),
                'player2': self.agents['player2'].get_action(current_state['player2'])
            }
            
            # Execute game step
            new_state, rewards = self.engine.step(actions['player1'], actions['player2'])
            
            # Get new state vectors
            new_state_vectors = {
                'player1': new_state.get_state_vector('player1'),
                'player2': new_state.get_state_vector('player2')
            }
            
            # Update agents
            for player_id in ['player1', 'player2']:
                self.agents[player_id].update(
                    current_state[player_id],
                    actions[player_id],
                    rewards[player_id],
                    new_state_vectors[player_id],
                    new_state.game_over
                )
            
            # Store episode data
            episode_data.append({
                'states': current_state,
                'actions': actions,
                'rewards': rewards,
                'new_states': new_state_vectors,
                'done': new_state.game_over
            })
        
        return {
            'winner': self.engine.state.winner,
            'episode_length': len(episode_data),
            'final_health': {
                'player1': self.engine.state.players['player1']['health'],
                'player2': self.engine.state.players['player2']['health']
            },
            'episode_data': episode_data
        }


@dataclass
class GameFrame:
    """Represents a single frame of game state for replay"""
    frame_number: int
    players: Dict[str, Dict]
    actions: Dict[str, str]  # Store action names as strings
    rewards: Dict[str, float]
    game_over: bool
    winner: Optional[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        frame_dict = asdict(self)
        # Convert Action enums to strings for JSON serialization
        return frame_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameFrame':
        """Create GameFrame from dictionary"""
        return cls(**data)

class ReplayRecorder:
    """Records game sessions for later replay"""
    
    def __init__(self, save_directory: str = "replays"):
        self.save_directory = save_directory
        self.current_recording = []
        self.is_recording = False
        self.recording_metadata = {}
        
        # Create replay directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)
    
    def start_recording(self, metadata: Dict[str, Any] = None):
        """Start recording a new game session"""
        self.is_recording = True
        self.current_recording = []
        self.recording_metadata = metadata or {}
        self.recording_metadata['start_time'] = datetime.now().isoformat()
    
    def record_frame(self, engine: GameEngine, actions: Dict[str, Action], 
                    rewards: Dict[str, float]):
        """Record a single frame of the game"""
        if not self.is_recording:
            return
        
        # Convert actions to string names for JSON serialization
        action_names = {player: action.name for player, action in actions.items()}
        
        frame = GameFrame(
            frame_number=engine.state.frame_count,
            players={
                'player1': dict(engine.state.players['player1']),
                'player2': dict(engine.state.players['player2'])
            },
            actions=action_names,
            rewards=rewards,
            game_over=engine.state.game_over,
            winner=engine.state.winner
        )
        
        self.current_recording.append(frame)
    
    def stop_recording(self) -> str:
        """Stop recording and save to file"""
        if not self.is_recording:
            return ""
        
        self.is_recording = False
        self.recording_metadata['end_time'] = datetime.now().isoformat()
        self.recording_metadata['total_frames'] = len(self.current_recording)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replay_{timestamp}.json"
        filepath = os.path.join(self.save_directory, filename)
        
        # Save to file
        replay_data = {
            'metadata': self.recording_metadata,
            'frames': [frame.to_dict() for frame in self.current_recording]
        }
        
        with open(filepath, 'w') as f:
            json.dump(replay_data, f, indent=2)
        
        print(f"Replay saved to {filepath}")
        return filepath

class ReplayPlayer:
    """Plays back recorded game sessions with visual rendering"""
    
    def __init__(self, replay_file: str):
        self.replay_file = replay_file
        self.frames = []
        self.metadata = {}
        self.current_frame_index = 0
        self.is_playing = False
        self.playback_speed = 1.0
        
        # Pygame setup for rendering
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Fighting Game Replay")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.colors = {
            'background': (50, 50, 50),
            'ground': (100, 100, 100),
            'player1': (0, 100, 255),
            'player2': (255, 100, 0),
            'health_bg': (100, 0, 0),
            'health_fg': (0, 255, 0),
            'ui_text': (255, 255, 255),
            'attack': (255, 255, 0),
            'block': (0, 255, 255)
        }
        
        self.load_replay()
    
    def load_replay(self):
        """Load replay data from file"""
        try:
            with open(self.replay_file, 'r') as f:
                replay_data = json.load(f)
            
            self.metadata = replay_data['metadata']
            self.frames = [GameFrame.from_dict(frame_data) 
                          for frame_data in replay_data['frames']]
            
            print(f"Loaded replay with {len(self.frames)} frames")
            
        except Exception as e:
            print(f"Error loading replay: {e}")
            self.frames = []
    
    def draw_player(self, player_data: Dict, player_id: str, x_offset: int = 0):
        """Draw a player on the screen"""
        x = int(player_data['x']) + x_offset
        y = int(player_data['y'])
        
        # Player body (rectangle)
        color = self.colors['player1'] if player_id == 'player1' else self.colors['player2']
        player_rect = pygame.Rect(x - 25, y - 50, 50, 50)
        pygame.draw.rect(self.screen, color, player_rect)
        
        # Draw facing direction indicator
        if player_data['facing_right']:
            pygame.draw.polygon(self.screen, (255, 255, 255), 
                              [(x + 25, y - 25), (x + 35, y - 25), (x + 30, y - 20)])
        else:
            pygame.draw.polygon(self.screen, (255, 255, 255),
                              [(x - 25, y - 25), (x - 35, y - 25), (x - 30, y - 20)])
        
        # Draw status indicators
        if player_data['is_attacking']:
            pygame.draw.circle(self.screen, self.colors['attack'], (x, y - 60), 8)
        
        if player_data['is_blocking']:
            pygame.draw.rect(self.screen, self.colors['block'], 
                           pygame.Rect(x - 30, y - 55, 60, 5))
        
        if player_data['is_jumping']:
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y - 70), 3)
    
    def draw_health_bar(self, health: float, x: int, y: int, width: int = 200):
        """Draw a health bar"""
        # Background
        bg_rect = pygame.Rect(x, y, width, 20)
        pygame.draw.rect(self.screen, self.colors['health_bg'], bg_rect)
        
        # Foreground (actual health)
        health_width = int((health / 100.0) * width)
        if health_width > 0:
            health_rect = pygame.Rect(x, y, health_width, 20)
            pygame.draw.rect(self.screen, self.colors['health_fg'], health_rect)
        
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 2)
        
        # Health text
        health_text = self.small_font.render(f"{int(health)}/100", True, self.colors['ui_text'])
        self.screen.blit(health_text, (x + width + 10, y))
    
    def draw_ui(self, frame: GameFrame):
        """Draw the user interface"""
        # Frame counter
        frame_text = self.small_font.render(f"Frame: {frame.frame_number}", True, self.colors['ui_text'])
        self.screen.blit(frame_text, (10, 10))
        
        # Playback speed
        speed_text = self.small_font.render(f"Speed: {self.playback_speed:.1f}x", True, self.colors['ui_text'])
        self.screen.blit(speed_text, (10, 35))
        
        # Player names and health bars
        p1_text = self.font.render("Player 1", True, self.colors['player1'])
        p2_text = self.font.render("Player 2", True, self.colors['player2'])
        
        self.screen.blit(p1_text, (50, 550))
        self.screen.blit(p2_text, (550, 550))
        
        self.draw_health_bar(frame.players['player1']['health'], 50, 570)
        self.draw_health_bar(frame.players['player2']['health'], 550, 570)
        
        # Actions
        action1_text = self.small_font.render(f"Action: {frame.actions['player1']}", 
                                            True, self.colors['ui_text'])
        action2_text = self.small_font.render(f"Action: {frame.actions['player2']}", 
                                            True, self.colors['ui_text'])
        
        self.screen.blit(action1_text, (260, 550))
        self.screen.blit(action2_text, (400, 550))
        
        # Game over indicator
        if frame.game_over:
            winner_text = self.font.render(f"Winner: {frame.winner}", True, (255, 255, 0))
            text_rect = winner_text.get_rect(center=(self.screen_width // 2, 50))
            self.screen.blit(winner_text, text_rect)
        
        # Controls
        controls = [
            "SPACE: Play/Pause",
            "LEFT/RIGHT: Frame by frame",
            "UP/DOWN: Speed control",
            "R: Restart",
            "ESC: Exit"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, (200, 200, 200))
            self.screen.blit(control_text, (10, 100 + i * 20))
    
    def draw_frame(self, frame: GameFrame):
        """Draw a single frame of the replay"""
        # Clear screen
        self.screen.fill(self.colors['background'])
        
        # Draw ground
        ground_y = 500  # Approximate ground level for rendering
        pygame.draw.rect(self.screen, self.colors['ground'], 
                        pygame.Rect(0, ground_y, self.screen_width, self.screen_height - ground_y))
        
        # Draw players
        self.draw_player(frame.players['player1'], 'player1')
        self.draw_player(frame.players['player2'], 'player2')
        
        # Draw UI
        self.draw_ui(frame)
        
        # Update display
        pygame.display.flip()
    
    def play_replay(self):
        """Main replay playback loop"""
        if not self.frames:
            print("No frames to play")
            return
        
        running = True
        self.is_playing = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing
                    
                    elif event.key == pygame.K_LEFT:
                        self.current_frame_index = max(0, self.current_frame_index - 1)
                    
                    elif event.key == pygame.K_RIGHT:
                        self.current_frame_index = min(len(self.frames) - 1, 
                                                     self.current_frame_index + 1)
                    
                    elif event.key == pygame.K_UP:
                        self.playback_speed = min(5.0, self.playback_speed + 0.5)
                    
                    elif event.key == pygame.K_DOWN:
                        self.playback_speed = max(0.1, self.playback_speed - 0.5)
                    
                    elif event.key == pygame.K_r:
                        self.current_frame_index = 0
                        self.is_playing = False
                    
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            # Auto-advance frames when playing
            if self.is_playing:
                self.current_frame_index += 1
                if self.current_frame_index >= len(self.frames):
                    self.current_frame_index = len(self.frames) - 1
                    self.is_playing = False
            
            # Draw current frame
            if self.frames:
                current_frame = self.frames[self.current_frame_index]
                self.draw_frame(current_frame)
            
            # Control playback speed
            self.clock.tick(60 * self.playback_speed)
        
        pygame.quit()

# Modified FightingGameFramework to support recording
class FightingGameFrameworkWithReplay(FightingGameFramework):
    """Extended framework with replay recording capability"""
    
    def __init__(self, agent1: MLAgent, agent2: MLAgent, record_replays: bool = True):
        super().__init__(agent1, agent2)
        self.record_replays = record_replays
        self.recorder = ReplayRecorder() if record_replays else None
    
    def run_episode(self, record: bool = None) -> Dict:
        """Run episode with optional recording"""
        should_record = record if record is not None else self.record_replays
        
        if should_record and self.recorder:
            metadata = {
                'agent1_type': type(self.agents['player1']).__name__,
                'agent2_type': type(self.agents['player2']).__name__
            }
            self.recorder.start_recording(metadata)
        
        self.engine.reset()
        episode_data = []
        
        while not self.engine.state.game_over:
            # Get current state
            current_state = {
                'player1': self.engine.state.get_state_vector('player1'),
                'player2': self.engine.state.get_state_vector('player2')
            }
            
            # Get actions from agents
            actions = {
                'player1': self.agents['player1'].get_action(current_state['player1']),
                'player2': self.agents['player2'].get_action(current_state['player2'])
            }
            
            # Execute game step
            new_state, rewards = self.engine.step(actions['player1'], actions['player2'])
            
            # Record frame if recording
            if should_record and self.recorder:
                self.recorder.record_frame(self.engine, actions, rewards)
            
            # Get new state vectors
            new_state_vectors = {
                'player1': new_state.get_state_vector('player1'),
                'player2': new_state.get_state_vector('player2')
            }
            
            # Update agents
            for player_id in ['player1', 'player2']:
                self.agents[player_id].update(
                    current_state[player_id],
                    actions[player_id],
                    rewards[player_id],
                    new_state_vectors[player_id],
                    new_state.game_over
                )
            
            # Store episode data
            episode_data.append({
                'states': current_state,
                'actions': actions,
                'rewards': rewards,
                'new_states': new_state_vectors,
                'done': new_state.game_over
            })
        
        # Stop recording and get filename
        replay_file = None
        if should_record and self.recorder:
            replay_file = self.recorder.stop_recording()
        
        return {
            'winner': self.engine.state.winner,
            'episode_length': len(episode_data),
            'final_health': {
                'player1': self.engine.state.players['player1']['health'],
                'player2': self.engine.state.players['player2']['health']
            },
            'episode_data': episode_data,
            'replay_file': replay_file
        }

# Example usage with replay functionality
if __name__ == "__main__":
    # Create agents
    agent1 = RandomAgent()
    agent2 = RandomAgent()
    
    # Create framework with replay recording
    framework = FightingGameFrameworkWithReplay(agent1, agent2, record_replays=True)
    
    # Run an episode and record it
    print("Running and recording episode...")
    result = framework.run_episode()
    print(f"Episode completed. Winner: {result['winner']}")
    print(f"Replay saved to: {result['replay_file']}")
    
    # Play back the replay
    if result['replay_file']:
        print("Starting replay player...")
        player = ReplayPlayer(result['replay_file'])
        player.play_replay()

# Previous imports and classes (Action, GameState, MLAgent, RandomAgent, etc.) remain the same

@dataclass
class AgentConfig:
    """Configuration for a learning agent"""
    # Feature selection
    include_features: Dict[str, bool] = field(default_factory=lambda: {
        'own_position': True,
        'own_health': True,
        'own_velocity': True,
        'own_state_flags': True,  # jumping, blocking, attacking
        'own_cooldowns': True,
        'opponent_position': True,
        'opponent_health': True,
        'opponent_velocity': True,
        'opponent_state_flags': True,
        'opponent_cooldowns': True,
        'relative_distance': True,
        'time_remaining': False,
        'health_difference': True,
        'height_difference': True,
    })
    
    # Network architecture
    hidden_layers: List[int] = field(default_factory=lambda: [256, 128, 64])
    activation: str = 'relu'  # 'relu', 'tanh', 'leaky_relu'
    dropout_rate: float = 0.1
    use_batch_norm: bool = True
    
    # Learning hyperparameters
    learning_rate: float = 0.001
    gamma: float = 0.99  # Discount factor
    epsilon_start: float = 1.0  # Exploration rate
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 32
    memory_size: int = 10000
    target_update_frequency: int = 100
    
    # Training settings
    train_frequency: int = 4  # Train every N steps
    min_memory_size: int = 1000  # Start training after this many experiences
    use_double_dqn: bool = True
    use_prioritized_replay: bool = False
    
    # Reward shaping
    reward_weights: Dict[str, float] = field(default_factory=lambda: {
        'health_change': 0.1,
        'damage_dealt': 0.2,
        'distance_penalty': -0.01,
        'win_bonus': 100.0,
        'lose_penalty': -100.0,
        'survival_bonus': 0.01,
        'aggressive_bonus': 0.05,  # For attacking
        'defensive_bonus': 0.03,   # For successful blocks
    })
    
    # Device settings
    use_cuda: bool = True
    
    def get_feature_size(self) -> int:
        """Calculate the size of the feature vector based on selected features"""
        feature_counts = {
            'own_position': 2,
            'own_health': 1,
            'own_velocity': 2,
            'own_state_flags': 3,
            'own_cooldowns': 1,
            'opponent_position': 2,
            'opponent_health': 1,
            'opponent_velocity': 2,
            'opponent_state_flags': 3,
            'opponent_cooldowns': 1,
            'relative_distance': 2,
            'time_remaining': 1,
            'health_difference': 1,
            'height_difference': 1,
        }
        
        total = 0
        for feature, include in self.include_features.items():
            if include and feature in feature_counts:
                total += feature_counts[feature]
        
        return total


class DQN(nn.Module):
    """Deep Q-Network with configurable architecture"""
    
    def __init__(self, input_size: int, output_size: int, config: AgentConfig):
        super(DQN, self).__init__()
        self.config = config
        
        # Build network layers
        layers = []
        prev_size = input_size
        
        # Hidden layers
        for i, hidden_size in enumerate(config.hidden_layers):
            layers.append(nn.Linear(prev_size, hidden_size))
            
            if config.use_batch_norm:
                layers.append(nn.BatchNorm1d(hidden_size))
            
            # Activation
            if config.activation == 'relu':
                layers.append(nn.ReLU())
            elif config.activation == 'tanh':
                layers.append(nn.Tanh())
            elif config.activation == 'leaky_relu':
                layers.append(nn.LeakyReLU())
            
            # Dropout
            if config.dropout_rate > 0:
                layers.append(nn.Dropout(config.dropout_rate))
            
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, output_size))
        
        self.network = nn.Sequential(*layers)
        
        # Dueling DQN architecture (optional)
        self.use_dueling = False  # Can be added as config option
        if self.use_dueling:
            self.value_stream = nn.Linear(config.hidden_layers[-1], 1)
            self.advantage_stream = nn.Linear(config.hidden_layers[-1], output_size)
    
    def forward(self, x):
        if self.use_dueling:
            features = self.network[:-1](x)  # All layers except last
            value = self.value_stream(features)
            advantage = self.advantage_stream(features)
            # Combine value and advantage streams
            q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
            return q_values
        else:
            return self.network(x)


class PrioritizedReplayBuffer:
    """Prioritized Experience Replay Buffer"""
    
    def __init__(self, capacity: int, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        
    def push(self, state, action, reward, next_state, done):
        max_priority = self.priorities.max() if self.buffer else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int, beta: float = 0.4):
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.position]
        
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        samples = [self.buffer[idx] for idx in indices]
        
        # Importance sampling weights
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-beta)
        weights /= weights.max()
        
        return samples, indices, torch.FloatTensor(weights)
    
    def update_priorities(self, indices, td_errors):
        for idx, td_error in zip(indices, td_errors):
            priority = abs(td_error) + 1e-6
            self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)


class DQNAgent(MLAgent):
    """Deep Q-Learning Agent with configurable features"""
    
    def __init__(self, config: AgentConfig, name: str = "DQNAgent"):
        self.config = config
        self.name = name
        self.device = torch.device("cuda" if config.use_cuda and torch.cuda.is_available() else "cpu")
        
        # Calculate input size based on selected features
        self.input_size = config.get_feature_size()
        self.output_size = len(Action)
        
        # Networks
        self.q_network = DQN(self.input_size, self.output_size, config).to(self.device)
        self.target_network = DQN(self.input_size, self.output_size, config).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=config.learning_rate)
        
        # Memory
        if config.use_prioritized_replay:
            self.memory = PrioritizedReplayBuffer(config.memory_size)
        else:
            self.memory = deque(maxlen=config.memory_size)
        
        # Training variables
        self.epsilon = config.epsilon_start
        self.steps_done = 0
        self.episodes_done = 0
        self.training_step = 0
        
        # Statistics
        self.loss_history = []
        self.reward_history = []
        self.epsilon_history = []
        
    def extract_features(self, state: np.ndarray) -> np.ndarray:
        """Extract selected features from the full state vector"""
        features = []
        
        # Assuming state vector structure from GameState.get_state_vector():
        # [0-8]: player1 data, [9-17]: player2 data, [18-19]: relative distances
        
        if self.config.include_features['own_position']:
            features.extend([state[0], state[1]])  # x, y
        
        if self.config.include_features['own_health']:
            features.append(state[2])
        
        if self.config.include_features['own_velocity']:
            features.extend([state[3], state[4]])
        
        if self.config.include_features['own_state_flags']:
            features.extend([state[5], state[6], state[7]])  # jumping, blocking, attacking
        
        if self.config.include_features['own_cooldowns']:
            features.append(state[8])
        
        if self.config.include_features['opponent_position']:
            features.extend([state[9], state[10]])
        
        if self.config.include_features['opponent_health']:
            features.append(state[11])
        
        if self.config.include_features['opponent_velocity']:
            features.extend([state[12], state[13]])
        
        if self.config.include_features['opponent_state_flags']:
            features.extend([state[14], state[15], state[16]])
        
        if self.config.include_features['opponent_cooldowns']:
            features.append(state[17])
        
        if self.config.include_features['relative_distance']:
            features.extend([state[18], state[19]])
        
        if self.config.include_features['time_remaining']:
            # Add time feature if needed (not in default state)
            features.append(0.0)  # Placeholder
        
        if self.config.include_features['health_difference']:
            features.append(state[2] - state[11])  # own health - opponent health
        
        if self.config.include_features['height_difference']:
            features.append(state[1] - state[10])  # own y - opponent y
        
        return np.array(features, dtype=np.float32)
    
    def get_action(self, state: np.ndarray) -> Action:
        """Select action using epsilon-greedy policy"""
        # Extract relevant features
        features = self.extract_features(state)
        
        # Epsilon-greedy action selection
        if random.random() < self.epsilon:
            return Action(random.randint(0, len(Action) - 1))
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor)
            return Action(q_values.argmax().item())
    
    def update(self, state: np.ndarray, action: Action, reward: float, 
               next_state: np.ndarray, done: bool):
        """Store experience and train the network"""
        # Extract features
        state_features = self.extract_features(state)
        next_state_features = self.extract_features(next_state)
        
        # Store transition
        if self.config.use_prioritized_replay:
            self.memory.push(state_features, action.value, reward, next_state_features, done)
        else:
            self.memory.append((state_features, action.value, reward, next_state_features, done))
        
        # Update steps counter
        self.steps_done += 1
        
        # Train the network
        if (len(self.memory) >= self.config.min_memory_size and 
            self.steps_done % self.config.train_frequency == 0):
            self._train_step()
        
        # Update target network
        if self.training_step % self.config.target_update_frequency == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Decay epsilon
        if done:
            self.episodes_done += 1
            self.epsilon = max(self.config.epsilon_end, 
                             self.epsilon * self.config.epsilon_decay)
            self.epsilon_history.append(self.epsilon)
    
    def _train_step(self):
        """Perform one training step"""
        if self.config.use_prioritized_replay:
            beta = min(1.0, 0.4 + self.training_step * (1.0 - 0.4) / 10000)
            transitions, indices, weights = self.memory.sample(self.config.batch_size, beta)
            weights = weights.to(self.device)
        else:
            transitions = random.sample(self.memory, self.config.batch_size)
            weights = torch.ones(self.config.batch_size).to(self.device)
        
        # Unpack transitions
        batch = list(zip(*transitions))
        states = torch.FloatTensor(batch[0]).to(self.device)
        actions = torch.LongTensor(batch[1]).to(self.device)
        rewards = torch.FloatTensor(batch[2]).to(self.device)
        next_states = torch.FloatTensor(batch[3]).to(self.device)
        dones = torch.FloatTensor(batch[4]).to(self.device)
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values
        with torch.no_grad():
            if self.config.use_double_dqn:
                # Double DQN: use online network to select action, target network to evaluate
                next_actions = self.q_network(next_states).argmax(1, keepdim=True)
                next_q_values = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            else:
                next_q_values = self.target_network(next_states).max(1)[0]
            
            target_q_values = rewards + (1 - dones) * self.config.gamma * next_q_values
        
        # Compute loss
        td_errors = target_q_values.unsqueeze(1) - current_q_values
        loss = (weights.unsqueeze(1)* td_errors.pow(2)).mean()
        
        # Update priorities if using prioritized replay
        if self.config.use_prioritized_replay:
            td_errors_np = td_errors.detach().cpu().numpy().squeeze()
            self.memory.update_priorities(indices, td_errors_np)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        self.training_step += 1
        self.loss_history.append(loss.item())
    
    def save(self, filepath: str):
        """Save the agent's model and configuration"""
        save_dict = {
            'config': asdict(self.config),
            'q_network_state': self.q_network.state_dict(),
            'target_network_state': self.target_network.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done,
            'episodes_done': self.episodes_done,
            'training_step': self.training_step,
            'loss_history': self.loss_history,
            'reward_history': self.reward_history,
            'epsilon_history': self.epsilon_history,
        }
        torch.save(save_dict, filepath)
        print(f"Agent saved to {filepath}")
    
    def load(self, filepath: str):
        """Load the agent's model and configuration"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        # Load configuration
        self.config = AgentConfig(**checkpoint['config'])
        
        # Rebuild networks if needed
        self.input_size = self.config.get_feature_size()
        self.q_network = DQN(self.input_size, self.output_size, self.config).to(self.device)
        self.target_network = DQN(self.input_size, self.output_size, self.config).to(self.device)
        
        # Load network states
        self.q_network.load_state_dict(checkpoint['q_network_state'])
        self.target_network.load_state_dict(checkpoint['target_network_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        
        # Load training state
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']
        self.episodes_done = checkpoint['episodes_done']
        self.training_step = checkpoint['training_step']
        self.loss_history = checkpoint['loss_history']
        self.reward_history = checkpoint['reward_history']
        self.epsilon_history = checkpoint['epsilon_history']
        
        print(f"Agent loaded from {filepath}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            'name': self.name,
            'episodes': self.episodes_done,
            'steps': self.steps_done,
            'epsilon': self.epsilon,
            'avg_loss': np.mean(self.loss_history[-100:]) if self.loss_history else 0,
            'avg_reward': np.mean(self.reward_history[-100:]) if self.reward_history else 0,
        }


class TrainingManager:
    """Manages the training process for agents"""
    
    def __init__(self, save_dir: str = "trained_agents"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.training_history = []
    
    def train_agents(self, agent1: DQNAgent, agent2: DQNAgent, 
                     num_episodes: int = 1000, save_frequency: int = 100):
        """Train two agents against each other"""
        framework = FightingGameFramework(agent1, agent2)
        
        for episode in range(num_episodes):
            result = framework.run_episode()
            
            # Track rewards
            agent1.reward_history.append(sum([r['rewards']['player1'] for r in result['episode_data']]))
            agent2.reward_history.append(sum([r['rewards']['player2'] for r in result['episode_data']]))
            
            # Print progress
            if episode % 10 == 0:
                stats1 = agent1.get_stats()
                stats2 = agent2.get_stats()
                print(f"Episode {episode}/{num_episodes}")
                print(f"  {stats1['name']}: ε={stats1['epsilon']:.3f}, "
                      f"avg_reward={stats1['avg_reward']:.2f}")
                print(f"  {stats2['name']}: ε={stats2['epsilon']:.3f}, "
                      f"avg_reward={stats2['avg_reward']:.2f}")
                print(f"  Winner: {result['winner']}, Length: {result['episode_length']}")
            
            # Save checkpoints
            if episode % save_frequency == 0 and episode > 0:
                self.save_checkpoint(agent1, agent2, episode)
        
        # Final save
        self.save_checkpoint(agent1, agent2, num_episodes)
        return agent1, agent2
    
    def save_checkpoint(self, agent1: DQNAgent, agent2: DQNAgent, episode: int):
        """Save training checkpoint"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        agent1_path = os.path.join(self.save_dir, f"{agent1.name}_ep{episode}_{timestamp}.pth")
        agent2_path = os.path.join(self.save_dir, f"{agent2.name}_ep{episode}_{timestamp}.pth")
        
        agent1.save(agent1_path)
        agent2.save(agent2_path)
        
        print(f"Checkpoint saved at episode {episode}")


# Example usage with different agent configurations
if __name__ == "__main__":
    # Configuration for an aggressive agent
    aggressive_config = AgentConfig(
        include_features={
            'own_position': True,
            'own_health': True,
            'own_velocity': True,
            'own_state_flags': True,
            'own_cooldowns': True,
            'opponent_position': True,
            'opponent_health': True,
            'opponent_velocity': False,
            'opponent_state_flags': True,
            'opponent_cooldowns': False,
            'relative_distance': True,
            'time_remaining': False,
            'health_difference': True,
            'height_difference': False,
        },
        hidden_layers=[128, 64],
        learning_rate=0.001,
        epsilon_decay=0.99,
        reward_weights={
            'health_change': 0.05,
            'damage_dealt': 0.3,  # High weight on dealing damage
            'distance_penalty': -0.02,  # Penalize being far
            'win_bonus': 100.0,
            'lose_penalty': -100.0,
            'survival_bonus': 0.01,
            'aggressive_bonus': 0.1,  # Bonus for attacking
            'defensive_bonus': 0.01,
        }
    )
    
    # Configuration for a defensive agent
    defensive_config = AgentConfig(
        include_features={
            'own_position': True,
            'own_health': True,
            'own_velocity': True,
            'own_state_flags': True,
            'own_cooldowns': True,
            'opponent_position': True,
            'opponent_health': True,
            'opponent_velocity': True,  # Track opponent movement
            'opponent_state_flags': True,
            'opponent_cooldowns': True,  # Track opponent cooldowns
            'relative_distance': True,
            'time_remaining': False,
            'health_difference': True,
            'height_difference': True,
        },
        hidden_layers=[256, 128, 64],  # Larger network
        learning_rate=0.0005,  # Slower learning
        epsilon_decay=0.995,
        reward_weights={
            'health_change': 0.2,  # High weight on preserving health
            'damage_dealt': 0.1,
            'distance_penalty': 0.0,  # No distance penalty
            'win_bonus': 100.0,
            'lose_penalty': -100.0,
            'survival_bonus': 0.05,  # Bonus for staying alive
            'aggressive_bonus': 0.01,
            'defensive_bonus': 0.1,  # High bonus for blocking
        }
    )
    
    # Create agents
    aggressive_agent = DQNAgent(aggressive_config, name="AggressiveBot")
    defensive_agent = DQNAgent(defensive_config, name="DefensiveBot")
    
    # Train agents
    trainer = TrainingManager()
    
    print("Training agents...")
    trained_aggressive, trained_defensive = trainer.train_agents(
        aggressive_agent, 
        defensive_agent,
        num_episodes=500,
        save_frequency=100
    )
    
    print("\nTraining complete!")
    print(f"Aggressive agent final stats: {trained_aggressive.get_stats()}")
    print(f"Defensive agent final stats: {trained_defensive.get_stats()}")
    
    # Test trained agents with recording
    print("\nTesting trained agents with replay recording...")
    framework = FightingGameFrameworkWithReplay(trained_aggressive, trained_defensive)
    
    # Set agents to evaluation mode (no exploration)
    trained_aggressive.epsilon = 0.0
    trained_defensive.epsilon = 0.0
    
    result = framework.run_episode(record=True)
    print(f"Test episode completed. Winner: {result['winner']}")
    
    if result['replay_file']:
        print(f"Replay saved to: {result['replay_file']}")
        print("Starting replay viewer...")
        player = ReplayPlayer(result['replay_file'])
        player.play_replay()