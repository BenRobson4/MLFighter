import pygame
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

class ReplayViewer:
    def __init__(self, replay_file: str):
        """Initialize the replay viewer with a replay file"""
        # Load replay data
        with open(replay_file, 'r') as f:
            self.replay_data = json.load(f)
        
        self.metadata = self.replay_data['metadata']
        self.frames = self.replay_data['frames']
        
        # Initialize Pygame
        pygame.init()
        
        # Set up display
        self.screen_width = self.metadata['arena_width']
        self.screen_height = self.metadata['arena_height']
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"Fight Replay: {self.metadata['player1_fighter']} vs {self.metadata['player2_fighter']}")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        self.DARK_RED = (139, 0, 0)
        self.DARK_BLUE = (0, 0, 139)
        
        # Player dimensions (from your PlayerState defaults)
        self.player_width = 50
        self.player_height = 100
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Replay control
        self.current_frame = 0
        self.playing = True
        self.speed_multiplier = 1.0
        
        # Font for UI
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Ground level
        self.ground_level = self.metadata['ground_level']
        
    def get_state_color(self, state: str) -> tuple:
        """Get color based on player state"""
        if 'ATTACK' in state:
            return self.RED
        elif 'BLOCK' in state:
            return self.GREEN
        elif 'JUMP' in state or 'RISING' in state or 'FALLING' in state:
            return self.YELLOW
        elif 'STUNNED' in state:
            return self.GRAY
        elif 'LEFT' in state or 'RIGHT' in state:
            return self.BLUE
        else:  # IDLE
            return self.WHITE
    
    def draw_player(self, player_data: Dict[str, Any], player_id: int):
        """Draw a player on the screen"""
        x = float(player_data['x'])
        y = float(player_data['y'])
        
        # When y=0, the feet should be at ground level
        ground_y = self.screen_height - self.ground_level
        feet_y = ground_y + y  # Add because negative y is up in game
        
        # Calculate top-left corner of rectangle for pygame
        screen_x = x - self.player_width // 2
        screen_y = feet_y - self.player_height  # Top of rectangle is height above feet
        
        # Get color based on state
        color = self.get_state_color(player_data['current_state'])
        
        # Draw player rectangle
        player_rect = pygame.Rect(screen_x, screen_y, self.player_width, self.player_height)
        pygame.draw.rect(self.screen, color, player_rect)
        
        # Draw player outline
        outline_color = self.DARK_BLUE if player_id == 1 else self.DARK_RED
        pygame.draw.rect(self.screen, outline_color, player_rect, 3)
        
        # Draw facing direction indicator
        if player_data['facing_right']:
            # Draw arrow pointing right
            pygame.draw.polygon(self.screen, outline_color, [
                (screen_x + self.player_width, screen_y + self.player_height // 2),
                (screen_x + self.player_width + 10, screen_y + self.player_height // 2),
                (screen_x + self.player_width + 10, screen_y + self.player_height // 2 - 5),
                (screen_x + self.player_width + 15, screen_y + self.player_height // 2 + 5),
                (screen_x + self.player_width + 10, screen_y + self.player_height // 2 + 15),
                (screen_x + self.player_width + 10, screen_y + self.player_height // 2 + 10),
                (screen_x + self.player_width, screen_y + self.player_height // 2 + 10)
            ])
        else:
            # Draw arrow pointing left
            pygame.draw.polygon(self.screen, outline_color, [
                (screen_x, screen_y + self.player_height // 2),
                (screen_x - 10, screen_y + self.player_height // 2),
                (screen_x - 10, screen_y + self.player_height // 2 - 5),
                (screen_x - 15, screen_y + self.player_height // 2 + 5),
                (screen_x - 10, screen_y + self.player_height // 2 + 15),
                (screen_x - 10, screen_y + self.player_height // 2 + 10),
                (screen_x, screen_y + self.player_height // 2 + 10)
            ])
        
        # Draw health bar above player
        health_percentage = float(player_data['health']) / 100.0  # Assuming max health is 100
        health_bar_width = self.player_width
        health_bar_height = 5
        health_bar_y = screen_y - 10
        
        # Background
        pygame.draw.rect(self.screen, self.RED, 
                        (screen_x, health_bar_y, health_bar_width, health_bar_height))
        # Health
        pygame.draw.rect(self.screen, self.GREEN, 
                        (screen_x, health_bar_y, health_bar_width * health_percentage, health_bar_height))
        
        # Draw player number
        player_text = self.small_font.render(f"P{player_id}", True, self.WHITE)
        text_rect = player_text.get_rect(center=(screen_x + self.player_width // 2, screen_y + self.player_height // 2))
        self.screen.blit(player_text, text_rect)
            
    def draw_ground(self):
        """Draw the ground line"""
        ground_y = self.screen_height - self.ground_level
        pygame.draw.line(self.screen, self.GRAY, (0, ground_y), (self.screen_width, ground_y), 3)
    
    def draw_ui(self):
        """Draw UI elements"""
        # Frame counter
        frame_text = self.font.render(f"Frame: {self.current_frame}/{len(self.frames)}", True, self.WHITE)
        self.screen.blit(frame_text, (10, 10))
        
        # Speed indicator
        speed_text = self.small_font.render(f"Speed: {self.speed_multiplier}x", True, self.WHITE)
        self.screen.blit(speed_text, (10, 50))
        
        # Player states
        if self.current_frame < len(self.frames):
            frame_data = self.frames[self.current_frame]
            
            # Player 1 state
            p1_state = frame_data['players']['1']['current_state']
            p1_text = self.small_font.render(f"P1: {p1_state}", True, self.DARK_BLUE)
            self.screen.blit(p1_text, (10, 80))
            
            # Player 2 state
            p2_state = frame_data['players']['2']['current_state']
            p2_text = self.small_font.render(f"P2: {p2_state}", True, self.DARK_RED)
            self.screen.blit(p2_text, (10, 105))
        
        # Controls
        controls = [
            "SPACE: Play/Pause",
            "LEFT/RIGHT: Step frames",
            "UP/DOWN: Speed control",
            "R: Restart",
            "Q: Quit"
        ]
        y_offset = self.screen_height - 150
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, self.WHITE)
            self.screen.blit(control_text, (10, y_offset + i * 25))
        
        # Winner display (if fight is over)
        if self.current_frame >= len(self.frames) - 1:
            winner = self.metadata.get('winner', 0)
            if winner > 0:
                winner_text = self.font.render(f"Player {winner} Wins!", True, self.YELLOW)
                text_rect = winner_text.get_rect(center=(self.screen_width // 2, 50))
                self.screen.blit(winner_text, text_rect)
            else:
                draw_text = self.font.render("Draw!", True, self.YELLOW)
                text_rect = draw_text.get_rect(center=(self.screen_width // 2, 50))
                self.screen.blit(draw_text, text_rect)
    
    def handle_input(self):
        """Handle keyboard input"""
        keys = pygame.key.get_pressed()
        
        # Frame stepping
        if keys[pygame.K_RIGHT] and not self.playing:
            self.current_frame = min(self.current_frame + 1, len(self.frames) - 1)
            pygame.time.wait(100)  # Debounce
        elif keys[pygame.K_LEFT] and not self.playing:
            self.current_frame = max(self.current_frame - 1, 0)
            pygame.time.wait(100)  # Debounce
        
        # Speed control
        if keys[pygame.K_UP]:
            self.speed_multiplier = min(self.speed_multiplier + 0.1, 5.0)
            pygame.time.wait(100)  # Debounce
        elif keys[pygame.K_DOWN]:
            self.speed_multiplier = max(self.speed_multiplier - 0.1, 0.1)
            pygame.time.wait(100)  # Debounce
        
        # Restart
        if keys[pygame.K_r]:
            self.current_frame = 0
            self.playing = False
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.playing = not self.playing
                    elif event.key == pygame.K_q:
                        running = False
            
            # Handle continuous input
            self.handle_input()
            
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Draw ground
            self.draw_ground()
            
            # Draw players if we have frame data
            if self.current_frame < len(self.frames):
                frame_data = self.frames[self.current_frame]
                
                # Draw both players
                self.draw_player(frame_data['players']['1'], 1)
                self.draw_player(frame_data['players']['2'], 2)
                
                # Advance frame if playing
                if self.playing:
                    frame_advance = self.speed_multiplier
                    self.current_frame += int(frame_advance)
                    if self.current_frame >= len(self.frames):
                        self.current_frame = len(self.frames) - 1
                        self.playing = False
            
            # Draw UI
            self.draw_ui()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python replay_viewer.py <replay_file.json>")
        print("\nControls:")
        print("  SPACE: Play/Pause")
        print("  LEFT/RIGHT: Step through frames (when paused)")
        print("  UP/DOWN: Increase/Decrease playback speed")
        print("  R: Restart replay")
        print("  Q: Quit")
        sys.exit(1)
    
    replay_file = sys.argv[1]
    
    if not Path(replay_file).exists():
        print(f"Error: Replay file '{replay_file}' not found")
        sys.exit(1)
    
    viewer = ReplayViewer(replay_file)
    viewer.run()


if __name__ == "__main__":
    main()