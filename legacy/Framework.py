import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
import pygame

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