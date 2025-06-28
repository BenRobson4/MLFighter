from typing import Dict, Optional, List
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
        
        # Set reward weights for each player in the engine
        for player_id, agent in self.agents.items():
            if hasattr(agent, 'config') and hasattr(agent.config, 'reward_weights'):
                self.engine.set_reward_weights(player_id, agent.config.reward_weights)
    
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
        all_reward_events = []  # Track all reward events
        
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
            
            # Execute game step - now returns events too
            new_state, rewards, events = self.engine.step(actions['player1'], actions['player2'])
            
            # Store reward events
            all_reward_events.extend(events)
            
            # Record frame if recording
            if should_record and self.recorder:
                self.recorder.record_frame(self.engine, actions, rewards)
            
            # Get new state vectors
            new_state_vectors = {
                'player1': new_state.get_state_vector('player1'),
                'player2': new_state.get_state_vector('player2')
            }
            
            # Create info dict with reward event details for each player
            info_dicts = {
                'player1': self._create_info_dict('player1', events),
                'player2': self._create_info_dict('player2', events)
            }
            
            # Update agents
            for player_id in ['player1', 'player2']:
                self.agents[player_id].update(
                    current_state[player_id],
                    actions[player_id],
                    rewards[player_id],
                    new_state_vectors[player_id],
                    new_state.game_over,
                    info_dicts[player_id]  # Pass the info dict
                )
            
            # Store episode data
            episode_data.append({
                'states': current_state,
                'actions': actions,
                'rewards': rewards,
                'new_states': new_state_vectors,
                'done': new_state.game_over,
                'events': events  # Include events in episode data
            })
        
        # Stop recording and get filename
        replay_file = None
        if should_record and self.recorder:
            replay_file = self.recorder.stop_recording()
        
        # Get reward summary from engine
        reward_summary = self.engine.reward_calculator.get_reward_summary()
        
        return {
            'winner': self.engine.state.winner,
            'episode_length': len(episode_data),
            'final_health': {
                'player1': self.engine.state.players['player1']['health'],
                'player2': self.engine.state.players['player2']['health']
            },
            'episode_data': episode_data,
            'replay_file': replay_file,
            'reward_events': all_reward_events,
            'reward_summary': reward_summary
        }
    
    def _create_info_dict(self, player_id: str, events: List) -> Dict:
        """Create info dictionary from reward events for a specific player"""
        info = {}
        
        # Extract relevant events for this player
        player_events = [e for e in events if e.player_id == player_id]
        
        # Aggregate events by type
        for event in player_events:
            if event.reward_type not in info:
                info[event.reward_type] = 0
            info[event.reward_type] += event.details.get('base_value', 0)
        
        return info
    
    def update_reward_weights(self, player_id: str, weights: Dict[str, float]):
        """Update reward weights for a specific player"""
        if player_id in self.agents:
            agent = self.agents[player_id]
            if hasattr(agent, 'config'):
                agent.config.update_reward_weights(weights)
            self.engine.set_reward_weights(player_id, weights)