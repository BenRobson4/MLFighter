import json
import pygame
from typing import Dict

from .recorder import GameFrame


class ReplayPlayer:
    """Plays back recorded game sessions with visual rendering"""
    
    def __init__(self, replay_file: str):
        self.replay_file = replay_file
        self.frames = []
        self.metadata = {}
        self.current_frame_index = 0
        self.is_playing = False
        self.playback_speed = 1.0
        self.max_healths = {}
        
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
            
            self.max_healths = {
                'player1': self.frames[0].players['player1']['health'],
                'player2': self.frames[0].players['player2']['health']
            }
            
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
    
    def draw_health_bar(self, health: float, max_health: float, x: int, y: int, width: int = 200):
        """Draw a health bar"""
        # Background
        bg_rect = pygame.Rect(x, y, width, 20)
        pygame.draw.rect(self.screen, self.colors['health_bg'], bg_rect)
        
        # Foreground (actual health)
        health_width = int((health / max_health) * width)
        if health_width > 0:
            health_rect = pygame.Rect(x, y, health_width, 20)
            pygame.draw.rect(self.screen, self.colors['health_fg'], health_rect)
        
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 2)
        
        # Health text
        health_text = self.small_font.render(f"{int(health)}/{max_health}", True, self.colors['ui_text'])
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

        
        self.draw_health_bar(frame.players['player1']['health'], self.max_healths['player1'], 50, 570)
        self.draw_health_bar(frame.players['player2']['health'], self.max_healths['player2'], 550, 570)
        
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