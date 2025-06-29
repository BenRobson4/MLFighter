import os
import sys
import time
import subprocess
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.data_classes import PlayerState
from core.globals import Action, State
from core.players.player_state_builder import PlayerStateBuilder
from core.players.player import Player
from core.game_loop import GameState, GameEngine


def create_player(player_id: int, fighter_name: str):
    """Create a player object with fighter data"""
    return Player(
        player_id=player_id, 
        fighter_name=fighter_name
    )


def setup_game():
    """Set up the game with two players"""
    # Create player objects with fighter data
    player1 = create_player(1, "balanced")
    player2 = create_player(2, "aggressive")
    
    # Build player states
    player1_state = PlayerStateBuilder.build(
        player1, 
        player_id=1, 
        spawn_x=None,  # Default spawn positions will be used
        spawn_y=None
    )
    player2_state = PlayerStateBuilder.build(
        player2, 
        player_id=2, 
        spawn_x=None,
        spawn_y=None
    )
    
    # Create game state
    state = GameState( 
        player1_state=player1_state, 
        player2_state=player2_state
    )

    # Create game engine with recording enabled
    engine = GameEngine(
        state=state,
        player_1=player1,
        player_2=player2,
        is_recording=True
    )
    
    return engine, state


def run_fight(engine, state):
    """Run a fight until completion"""
    print("Starting fight...")
    start_time = time.time()
    frame_count = 0
    
    # Run until fight is over
    while not engine.fight_over:
        engine.step(state)
        frame_count += 1
        
        # Print progress every 100 frames
        if frame_count % 100 == 0:
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            print(f"Frame {frame_count}, {fps:.1f} FPS, Player 1 Health: {state.get_player(1).health:.1f}, Player 2 Health: {state.get_player(2).health:.1f}")
    
    # Fight is over
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    print("\nFight completed!")
    print(f"Total frames: {frame_count}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Average FPS: {fps:.1f}")
    print(f"Winner: Player {engine.winner}")
    print(f"Final health - P1: {state.get_player(1).health:.1f}, P2: {state.get_player(2).health:.1f}")
    
    # Return the last saved replay file
    replay_dir = Path("replays")
    if replay_dir.exists():
        replay_files = list(replay_dir.glob("*.json"))
        if replay_files:
            latest_replay = max(replay_files, key=lambda p: p.stat().st_mtime)
            return str(latest_replay)
    
    return None


def view_replay(replay_file):
    """Launch the replay viewer for the generated replay"""
    if not replay_file or not Path(replay_file).exists():
        print("No replay file found.")
        return
    
    viewer_path = Path(__file__).parent / "replay_viewer.py"
    if not viewer_path.exists():
        print("Replay viewer not found. Please ensure replay_viewer.py is in the same directory.")
        return
    
    print(f"\nLaunching replay viewer for: {replay_file}")
    
    try:
        subprocess.run([sys.executable, str(viewer_path), replay_file])
    except Exception as e:
        print(f"Error launching replay viewer: {e}")


def main():
    """Main entry point"""
    print("ML Fighting Game - Fight Generator")
    print("=================================\n")
    
    # Setup game
    engine, state = setup_game()
    
    # Run fight
    replay_file = run_fight(engine, state)
    
    # Ask if user wants to view the replay
    if replay_file:
        response = input("\nDo you want to view the replay? (y/n): ")
        if response.lower().startswith('y'):
            view_replay(replay_file)
    
    print("\nDone.")


if __name__ == "__main__":
    main()