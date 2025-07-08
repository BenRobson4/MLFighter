import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import random
from typing import List, Optional, Tuple
import numpy as np


class DQNetwork(nn.Module):
    """Fixed architecture DQN"""
    
    def __init__(self, input_size: int, output_size: int):
        super(DQNetwork, self).__init__()
        
        # Fixed architecture
        self.network = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, output_size)
        )
    
    def forward(self, x, feature_mask=None):
        """Forward pass with optional feature masking"""
        if feature_mask is not None:
            x = x * feature_mask
        return self.network(x)


class MLAgent:
    """Base DQN Agent focused on core functionality"""
    
    def __init__(self, 
                 num_features: int,
                 num_actions: int,
                 epsilon: float = 1.0,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01,
                 learning_rate: float = 0.001,
                 initial_feature_mask: Optional[np.ndarray] = None,
                 device: str = None
                 ):
        
        # Core parameters
        self.num_features = num_features
        self.num_actions = num_actions
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.learning_rate = learning_rate
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Fixed training parameters
        self.gamma = 0.99
        self.memory_size = 10000
        self.batch_size = 32
        self.update_frequency = 4
        self.target_update_frequency = 100
        
        # Neural networks
        self.q_network = DQNetwork(num_features, num_actions).to(self.device)
        self.target_network = DQNetwork(num_features, num_actions).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Experience replay
        self.memory = deque(maxlen=self.memory_size)
        
        # Training state
        self.steps = 0
        self.episodes = 0
        
        # Feature mask (default: all features active)
        # Feature mask (default: all features active if not provided)
        if initial_feature_mask is not None:
            self.feature_mask = torch.FloatTensor(initial_feature_mask).to(self.device)
        else:
            self.feature_mask = torch.ones(num_features).to(self.device)

    
    def get_action(self, 
                   state: np.ndarray, 
                   available_actions: Optional[List[int]] = None,
                   epsilon: Optional[float] = None) -> int:
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current state vector
            available_actions: List of valid action indices (if None, all actions valid)
            epsilon: Override epsilon for this action (if None, use self.epsilon)
        
        Returns:
            Selected action index
        """
        eps = epsilon if epsilon is not None else self.epsilon
        
        # Get valid actions
        if available_actions is None:
            available_actions = list(range(self.num_actions))
        
        # Epsilon-greedy selection
        if random.random() < eps:
            return random.choice(available_actions)
        
        # Get Q-values
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor, self.feature_mask).squeeze(0)
            
            # Mask invalid actions
            masked_q = q_values.clone()
            for i in range(self.num_actions):
                if i not in available_actions:
                    masked_q[i] = float('-inf')
            
            return masked_q.argmax().item()
    
    def update(self, 
               state: np.ndarray, 
               action: int, 
               reward: float,
               next_state: np.ndarray, 
               done: bool):
        """
        Update the agent with new experience
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received (already shaped by child class)
            next_state: Next state
            done: Whether episode ended
        """
        # Store experience
        self.memory.append((state, action, reward, next_state, done))
        
        # Update step counter
        self.steps += 1
        
        # Update epsilon on episode end
        if done:
            self.episodes += 1
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Train if enough samples
        if len(self.memory) >= self.batch_size and self.steps % self.update_frequency == 0:
            self._train_step()
        
        # Update target network
        if self.steps % self.target_update_frequency == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
    
    def _train_step(self):
        """Perform one training step"""
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        
        # Prepare tensors
        states = torch.FloatTensor([e[0] for e in batch]).to(self.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.device)
        dones = torch.FloatTensor([e[4] for e in batch]).to(self.device)
        
        # Apply feature masks
        states = states * self.feature_mask
        next_states = next_states * self.feature_mask
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values (Double DQN)
        with torch.no_grad():
            next_actions = self.q_network(next_states).argmax(dim=1, keepdim=True)
            next_q_values = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            targets = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Loss and optimization
        loss = F.mse_loss(current_q_values.squeeze(), targets)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
    
    def update_parameters(self,
                         epsilon: Optional[float] = None,
                         epsilon_decay: Optional[float] = None,
                         learning_rate: Optional[float] = None,
                         feature_mask: Optional[np.ndarray] = None):
        """
        Update agent parameters without affecting network weights
        
        Args:
            epsilon: New epsilon value
            epsilon_decay: New epsilon decay rate
            learning_rate: New learning rate
            feature_mask: Binary mask for active features
        """
        if epsilon is not None:
            self.epsilon = epsilon
        
        if epsilon_decay is not None:
            self.epsilon_decay = epsilon_decay
        
        if learning_rate is not None:
            self.learning_rate = learning_rate
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = learning_rate
        
        if feature_mask is not None:
            self.feature_mask = torch.FloatTensor(feature_mask).to(self.device)
    
    def save_weights(self, filepath: str):
        """Save network weights and training state"""
        torch.save({
            'q_network_state': self.q_network.state_dict(),
            'target_network_state': self.target_network.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'steps': self.steps,
            'episodes': self.episodes,
            'epsilon': self.epsilon,
            'memory': list(self.memory)[-1000:]  # Save last 1000 experiences
        }, filepath)
    
    def load_weights(self, filepath: str):
        """Load network weights while keeping current parameters"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network_state'])
        self.target_network.load_state_dict(checkpoint['target_network_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        
        # Restore training state
        self.steps = checkpoint.get('steps', 0)
        self.episodes = checkpoint.get('episodes', 0)
        
        # Optionally restore memory
        if 'memory' in checkpoint:
            for exp in checkpoint['memory']:
                self.memory.append(tuple(exp))
    
    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """Get Q-values for a state (useful for debugging)"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor, self.feature_mask)
            return q_values.cpu().numpy().squeeze()