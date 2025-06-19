import pygame
from typing import List
from ..replay import ReplayPlayer, GameFrame
import json


class MultiReplayPlayer(ReplayPlayer):
    """Extended replay player that handles multiple replays in sequence"""
    
    def __init__(self, replay_files: List[str]):
        self.replay_files = replay_files
        self.current_replay_index = 0
        self.all_replays = []
        
        # Load first replay to initialize
        super().__init__(replay_files[0])
        
        # Load all replays
        self.load_all_replays()
    
    def load_all_replays(self):
        """Load all replay files"""
        self.all_replays = []
        
        for replay_file in self.replay_files:
            try:
                with open(replay_file, 'r') as f:
                    replay_data = json.load(f)
                
                frames = [GameFrame.from_dict(frame_data) 
                         for frame_data in replay_data['frames']]
                
                self.all_replays.append({
                    'file': replay_file,
                    'metadata': replay_data['metadata'],
                    'frames': frames
                })
                
            except Exception as e:
                print(f"Error loading replay {replay_file}: {e}")
        
        print(f"Loaded {len(self.all_replays)} replays")
    
    def switch_replay(self, index: int):
        """Switch to a different replay"""
        if 0 <= index < len(self.all_replays):
            self.current_replay_index = index
            replay = self.all_replays[index]
            self.frames = replay['frames']
            self.metadata = replay['metadata']
            self.current_frame_index = 0
            print(f"Switched to replay {index + 1}/{len(self.all_replays)}")
    
    def draw_multi_ui(self, frame: GameFrame):
        """Draw UI with multi-replay information"""
        # Call parent UI
        super().draw_ui(frame)
        
        # Add replay counter
        replay_text = self.font.render(
            f"Replay {self.current_replay_index + 1}/{len(self.all_replays)}", 
            True, (255, 255, 0)
        )
        self.screen.blit(replay_text, (self.screen_width - 200, 10))
        
        # Add additional controls info
        control_text = self.small_font.render(
            "N: Next replay, P: Previous replay", 
            True, (200, 200, 200)
        )
        self.screen.blit(control_text, (10, 220))
    
    def play_all(self):
        """Play all replays in sequence"""
        if not self.all_replays:
            print("No replays to play")
            return
        
        running = True
        self.is_playing = True
        auto_advance = True
        
        # Start with first replay
        self.switch_replay(0)
        
        clock = pygame.time.Clock()
        
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
                    
                    elif event.key == pygame.K_n:
                        # Next replay
                        if self.current_replay_index < len(self.all_replays) - 1:
                            self.switch_replay(self.current_replay_index + 1)
                            self.is_playing = True
                    
                    elif event.key == pygame.K_p:
                        # Previous replay
                        if self.current_replay_index > 0:
                            self.switch_replay(self.current_replay_index - 1)
                            self.is_playing = True
                    
                    elif event.key == pygame.K_a:
                        # Toggle auto-advance
                        auto_advance = not auto_advance
                        print(f"Auto-advance: {auto_advance}")
                    
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            # Auto-advance frames when playing
            if self.is_playing and self.frames:
                self.current_frame_index += 1
                
                # Check if current replay ended
                if self.current_frame_index >= len(self.frames):
                    if auto_advance and self.current_replay_index < len(self.all_replays) - 1:
                        # Auto-advance to next replay
                        self.switch_replay(self.current_replay_index + 1)
                        self.is_playing = True
                    else:
                        # Stop at end of replay
                        self.current_frame_index = len(self.frames) - 1
                        self.is_playing = False
            
            # Draw current frame
            if self.frames:
                current_frame = self.frames[self.current_frame_index]
                self.draw_frame(current_frame)
                self.draw_multi_ui(current_frame)  # Use extended UI
            
            pygame.display.flip()
            clock.tick(60 * self.playback_speed)
        
        pygame.quit()