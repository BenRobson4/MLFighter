from typing import Dict, Optional
from ..core import GameEngine, Action
from ..agents import MLAgent
from ..replay import ReplayRecorder


class FightingGameFramework:
    """Main framework class that orchestrates the fighting game"""
    
    def __init__(self, agent1: MLAgent, agent2: MLAgent, record_replays: bool = False, 
                 player1_fighter: str = 'Default', player2_fighter: str = 'Default'):
        self.engine = GameEngine(player1_fighter=player1_fighter, player2_fighter=player2_fighter)
        self.agents = {'player1': agent1, 'player2': agent2}
        self.game_history = []
        self.record_replays = record_replays
        self.recorder = ReplayRecorder() if record_replays else None
    
    def run_episode(self, record: Optional[bool] = None) -> Dict:
        """Run a complete game episode"""
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