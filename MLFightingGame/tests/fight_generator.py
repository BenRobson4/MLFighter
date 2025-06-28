"""
Fight Generator - Runs a single fight between two AI players and saves the replay
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ..core.data_classes import PlayerState, Fighter
from ..core.globals import Action, State
from ..core.players.player_state_builder import PlayerStateBuilder
from ..core.players.player import Player
from ..core.game_loop import GameState, GameEngine


class FightGenerator:
    """Generates and runs a single fight between two players"""
    
    def __init__(self, 
                 player1_fighter: str = "balanced",
                 player2_fighter: str = "aggressive",
                 arena_width: int = 800,
                 arena_height: int = 400,
                 record_replay: bool = True,
                 max_frames: int = 1800):  # 30 seconds at 60 FPS
        """
        Initialize the fight generator
        
        Args:
            player1_fighter: Fighter type for player 1
            player2_fighter: Fighter type for player 2
            arena_width: Width of the arena
            arena_height: Height of the arena
            record_replay: Whether to record the fight for replay
            max_frames: Maximum frames before timeout
        """
        self.player1_fighter = player1_fighter
        self.player2_fighter = player2_fighter
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.record_replay = record_replay
        self.max_frames = max_frames
        
        self.setup_fight()
    
    def setup_fight(self):
        """Set up the fight with players and game engine"""
        # Create players
        print(f"Creating Player 1: {self.player1_fighter}")
        self.player1 = Player(
            player_id=1, 
            fighter_name=self.player1_fighter
        )
        
        print(f"Creating Player 2: {self.player2_fighter}")
        self.player2 = Player(
            player_id=2, 
            fighter_name=self.player2_fighter
        )
        
        # Build player states with spawn positions
        spawn_margin = 250  # Distance from center
        center_x = self.arena_width / 2
        
        self.player1_state = PlayerStateBuilder.build(
            self.player1, 
            player_id=1, 
            spawn_x=center_x - spawn_margin, 
            spawn_y=0.0
        )
        
        self.player2_state = PlayerStateBuilder.build(
            self.player2, 
            player_id=2, 
            spawn_x=center_x + spawn_margin, 
            spawn_y=0.0
        )
        
        # Create game state
        self.game_state = GameState(
            arena_width=self.arena_width, 
            arena_height=self.arena_height, 
            player1_state=self.player1_state, 
            player2_state=self.player2_state
        )
        
        # Create game engine
        self.engine = GameEngine(
            state=self.game_state,
            player_1=self.player1,
            player_2=self.player2,
            is_recording=False  # Will be set before running
        )
    
    def run_fight(self) -> dict:
        """
        Run the fight until completion
        
        Returns:
            Dictionary with fight results
        """
        print(f"\n{'='*50}")
        print(f"Starting fight: {self.player1_fighter} vs {self.player2_fighter}")
        print(f"Arena: {self.arena_width}x{self.arena_height}")
        print(f"Recording: {'Enabled' if self.record_replay else 'Disabled'}")
        print(f"{'='*50}\n")
        
        # Enable recording if requested
        if self.record_replay:
            self.engine.set_recording(True)
        
        # Run the fight
        frame_count = 0
        
        while not self.engine.fight_over and frame_count < self.max_frames:
            # Step the game engine
            self.engine.step(self.game_state)
            frame_count += 1
            
            # Print progress every 60 frames (1 second at 60 FPS)
            if frame_count % 60 == 0:
                p1_health = self.player1_state.health
                p2_health = self.player2_state.health
                print(f"Frame {frame_count}: P1 Health: {p1_health:.1f}, P2 Health: {p2_health:.1f}")
        
        # Fight ended
        print(f"\n{'='*50}")
        print(f"Fight ended after {frame_count} frames ({frame_count/60:.1f} seconds)")
        
        # Determine results
        results = {
            'total_frames': frame_count,
            'duration_seconds': frame_count / 60,
            'winner': self.engine.winner,
            'player1_health': self.player1_state.health,
            'player2_health': self.player2_state.health,
            'player1_fighter': self.player1_fighter,
            'player2_fighter': self.player2_fighter,
            'timeout': frame_count >= self.max_frames
        }
        
        # Print results
        if results['timeout']:
            print("Fight ended due to timeout!")
        
        if results['winner'] == 1:
            print(f"Winner: Player 1 ({self.player1_fighter})")
        elif results['winner'] == 2:
            print(f"Winner: Player 2 ({self.player2_fighter})")
        else:
            print("Draw!")
        
        print(f"Final Health - P1: {results['player1_health']:.1f}, P2: {results['player2_health']:.1f}")
        
        if self.record_replay:
            print("\nReplay saved to 'replays' directory")
        
        print(f"{'='*50}\n")
        
        return results
    
    def reset_and_run_another(self) -> dict:
        """Reset the engine and run another fight"""
        print("Resetting for another fight...")
        self.engine.reset()
        
        # Re-enable recording if needed
        if self.record_replay:
            self.engine.set_recording(True)
        
        return self.run_fight()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate a fight between two AI players')
    parser.add_argument('--p1', '--player1', 
                       default='balanced',
                       help='Fighter type for Player 1 (default: balanced)')
    parser.add_argument('--p2', '--player2',
                       default='aggressive', 
                       help='Fighter type for Player 2 (default: aggressive)')
    parser.add_argument('--width',
                       type=int,
                       default=800,
                       help='Arena width (default: 800)')
    parser.add_argument('--height',
                       type=int,
                       default=400,
                       help='Arena height (default: 400)')
    parser.add_argument('--no-record',
                       action='store_true',
                       help='Disable replay recording')
    parser.add_argument('--max-frames',
                       type=int,
                       default=1800,
                       help='Maximum frames before timeout (default: 1800)')
    parser.add_argument('--multiple',
                       type=int,
                       default=1,
                       help='Number of fights to run (default: 1)')
    
    args = parser.parse_args()
    
    # Create fight generator
    generator = FightGenerator(
        player1_fighter=args.p1,
        player2_fighter=args.p2,
        arena_width=args.width,
        arena_height=args.height,
        record_replay=not args.no_record,
        max_frames=args.max_frames
    )
    
    # Run multiple fights if requested
    all_results = []
    for i in range(args.multiple):
        if i > 0:
            print(f"\n{'#'*60}")
            print(f"Fight {i+1} of {args.multiple}")
            print(f"{'#'*60}\n")
            results = generator.reset_and_run_another()
        else:
            results = generator.run_fight()
        all_results.append(results)
    
    # Print summary if multiple fights
    if args.multiple > 1:
        print(f"\n{'='*60}")
        print("SUMMARY OF ALL FIGHTS")
        print(f"{'='*60}")
        
        p1_wins = sum(1 for r in all_results if r['winner'] == 1)
        p2_wins = sum(1 for r in all_results if r['winner'] == 2)
        draws = sum(1 for r in all_results if r['winner'] not in [1, 2])
        
        print(f"Total Fights: {args.multiple}")
        print(f"Player 1 ({args.p1}) Wins: {p1_wins} ({p1_wins/args.multiple*100:.1f}%)")
        print(f"Player 2 ({args.p2}) Wins: {p2_wins} ({p2_wins/args.multiple*100:.1f}%)")
        print(f"Draws: {draws} ({draws/args.multiple*100:.1f}%)")
        
        avg_duration = sum(r['duration_seconds'] for r in all_results) / len(all_results)
        print(f"\nAverage Fight Duration: {avg_duration:.1f} seconds")
        
        avg_p1_health = sum(r['player1_health'] for r in all_results) / len(all_results)
        avg_p2_health = sum(r['player2_health'] for r in all_results) / len(all_results)
        print(f"Average Final Health - P1: {avg_p1_health:.1f}, P2: {avg_p2_health:.1f}")
        
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()