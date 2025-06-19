import os
from typing import List, Dict, Any
import numpy as np

from ..agents import DQNAgent
from ..framework import FightingGameFramework


class TrainingManager:
    """Manages training of agents with different configurations"""
    
    def __init__(self, save_dir: str = "models"):
        self.training_history = []
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    def train_agents(self, agent1: DQNAgent, agent2: DQNAgent, 
                     num_episodes: int, save_frequency: int = 100,
                     record_frequency: int = 100) -> List[Dict[str, Any]]:
        """Train two agents against each other"""
        framework = FightingGameFramework(agent1, agent2, record_replays=False)
        
        for episode in range(num_episodes):
            # Run episode (record occasionally)
            should_record = (episode % record_frequency == 0)
            result = framework.run_episode(record=should_record)
            
            # Store training data
            self.training_history.append({
                'episode': episode,
                'winner': result['winner'],
                'episode_length': result['episode_length'],
                'final_health': result['final_health'],
                'agent1_stats': agent1.get_stats(),
                'agent2_stats': agent2.get_stats()
            })
            
            # Print progress
            if episode % 10 == 0:
                recent_history = self.training_history[-100:]
                win_rate_1 = sum(1 for h in recent_history 
                                if h['winner'] == 'player1') / len(recent_history)
                print(f"Episode {episode}: Win rate P1: {win_rate_1:.2%}, "
                      f"Epsilon P1: {agent1.epsilon:.3f}, P2: {agent2.epsilon:.3f}")
            
            # Save models periodically
            if episode % save_frequency == 0 and episode > 0:
                agent1_path = os.path.join(self.save_dir, f"agent1_episode_{episode}.pth")
                agent2_path = os.path.join(self.save_dir, f"agent2_episode_{episode}.pth")
                agent1.save(agent1_path)
                agent2.save(agent2_path)
                print(f"Saved models at episode {episode}")
        
        return self.training_history
    
    def evaluate_agents(self, agent1: DQNAgent, agent2: DQNAgent, 
                       num_episodes: int = 10) -> Dict[str, Any]:
        """Evaluate agents without training"""
        # Disable exploration
        original_epsilon1 = agent1.epsilon
        original_epsilon2 = agent2.epsilon
        agent1.epsilon = 0
        agent2.epsilon = 0
        
        framework = FightingGameFramework(agent1, agent2, record_replays=True)
        results = []
        
        for i in range(num_episodes):
            result = framework.run_episode(record=(i == 0))  # Record first match
            results.append(result)
            print(f"Evaluation {i+1}: Winner: {result['winner']}, "
                  f"Health: P1={result['final_health']['player1']}, "
                  f"P2={result['final_health']['player2']}")
        
        #Restore original epsilon values
        agent1.epsilon = original_epsilon1
        agent2.epsilon = original_epsilon2
        
        # Calculate statistics
        p1_wins = sum(1 for r in results if r['winner'] == 'player1')
        avg_episode_length = np.mean([r['episode_length'] for r in results])
        
        return {
            'player1_wins': p1_wins,
            'player2_wins': num_episodes - p1_wins,
            'win_rate_player1': p1_wins / num_episodes,
            'avg_episode_length': avg_episode_length,
            'results': results
        }