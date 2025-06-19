"""
Main entry point for the Fighting Game ML Framework
"""

import argparse
from .ui.game_manager import GameManager


def main():
    parser = argparse.ArgumentParser(description='Fighting Game ML Framework')
    parser.add_argument('--rounds', type=int, default=250,
                       help='Number of rounds per phase (default: 250)')
    parser.add_argument('--replays', type=int, default=5,
                       help='Number of replays to show (default: 5)')
    
    args = parser.parse_args()
    
    # Create and run game manager
    manager = GameManager(rounds_per_phase=args.rounds, replays_to_show=args.replays)
    manager.run_game()


if __name__ == '__main__':
    main()