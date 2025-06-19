import tkinter as tk
from tkinter import ttk
from typing import Dict, Set, Callable
import json


class AgentConfigUI:
    """UI for configuring agent features and rewards"""
    
    def __init__(self, player_name: str, initial_config: 'AdaptiveConfig', 
                 on_submit: Callable):
        self.player_name = player_name
        self.config = initial_config
        self.on_submit = on_submit
        
        self.root = tk.Tk()
        self.root.title(f"{player_name} Configuration")
        self.root.geometry("800x700")
        
        # Store UI variables
        self.feature_vars = {}
        self.reward_vars = {}
        self.learning_vars = {}
        
        self.create_ui()
    
    def create_ui(self):
        """Create the configuration UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text=f"{self.player_name} Configuration", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Features section
        self.create_features_section(main_frame, row=1)
        
        # Rewards section
        self.create_rewards_section(main_frame, row=2)
        
        # Learning parameters section
        self.create_learning_section(main_frame, row=3)
        
        # Submit button
        submit_btn = ttk.Button(main_frame, text="Apply Configuration", 
                               command=self.submit_config)
        submit_btn.grid(row=4, column=0, columnspan=2, pady=20)
    
    def create_features_section(self, parent, row):
        """Create feature selection section"""
        frame = ttk.LabelFrame(parent, text="Feature Selection", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Create checkboxes in 3 columns
        features = self.config.all_features
        cols = 3
        for i, feature in enumerate(features):
            var = tk.BooleanVar(value=feature in self.config.active_features)
            self.feature_vars[feature] = var
            
            cb = ttk.Checkbutton(frame, text=feature.replace('_', ' ').title(), 
                                variable=var, command=self.on_feature_toggle)
            cb.grid(row=i // cols, column=i % cols, sticky=tk.W, padx=5, pady=2)
    
    def create_rewards_section(self, parent, row):
        """Create reward weights section"""
        frame = ttk.LabelFrame(parent, text="Reward Weights", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        reward_labels = {
            'health_gain': 'Health Gain',
            'damage_dealt': 'Damage Dealt',
            'win_bonus': 'Win Bonus',
            'loss_penalty': 'Loss Penalty',
            'distance_bonus': 'Distance Bonus',
            'aggression_bonus': 'Aggression Bonus',
            'defense_bonus': 'Defense Bonus'
        }
        
        for i, (key, label) in enumerate(reward_labels.items()):
            # Label
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky=tk.W, padx=5)
            
            # Current value label
            value_label = ttk.Label(frame, text=f"{self.config.reward_weights[key]:.2f}")
            value_label.grid(row=i, column=2, padx=5)
            
            # Slider
            var = tk.DoubleVar(value=self.config.reward_weights[key])
            self.reward_vars[key] = var
            
            # Determine slider range
            if 'penalty' in key:
                from_val, to_val = -200, 0
            elif 'bonus' in key:
                from_val, to_val = 0, 200
            else:
                from_val, to_val = -10, 10
            
            slider = ttk.Scale(frame, from_=from_val, to=to_val, variable=var,
                              command=lambda v, lbl=value_label, vr=var: 
                              lbl.config(text=f"{vr.get():.2f}"))
            slider.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5)
            
            # Disable if feature not active
            if key in ['distance_bonus'] and 'distance_x' not in self.config.active_features:
                slider.config(state='disabled')
    
    def create_learning_section(self, parent, row):
        """Create learning parameters section"""
        frame = ttk.LabelFrame(parent, text="Learning Parameters", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Epsilon
        ttk.Label(frame, text="Epsilon (Exploration):").grid(row=0, column=0, sticky=tk.W)
        epsilon_var = tk.DoubleVar(value=self.config.epsilon)
        self.learning_vars['epsilon'] = epsilon_var
        epsilon_scale = ttk.Scale(frame, from_=0.0, to=1.0, variable=epsilon_var)
        epsilon_scale.grid(row=0, column=1, sticky=(tk.W, tk.E))
        epsilon_label = ttk.Label(frame, text=f"{self.config.epsilon:.3f}")
        epsilon_label.grid(row=0, column=2)
        epsilon_scale.config(command=lambda v: epsilon_label.config(text=f"{float(v):.3f}"))
        
        # Epsilon decay
        ttk.Label(frame, text="Epsilon Decay:").grid(row=1, column=0, sticky=tk.W)
        decay_var = tk.DoubleVar(value=self.config.epsilon_decay)
        self.learning_vars['epsilon_decay'] = decay_var
        decay_scale = ttk.Scale(frame, from_=0.9, to=1.0, variable=decay_var)
        decay_scale.grid(row=1, column=1, sticky=(tk.W, tk.E))
        decay_label = ttk.Label(frame, text=f"{self.config.epsilon_decay:.4f}")
        decay_label.grid(row=1, column=2)
        decay_scale.config(command=lambda v: decay_label.config(text=f"{float(v):.4f}"))
        
        # Learning rate
        ttk.Label(frame, text="Learning Rate:").grid(row=2, column=0, sticky=tk.W)
        lr_var = tk.DoubleVar(value=self.config.learning_rate)
        self.learning_vars['learning_rate'] = lr_var
        lr_scale = ttk.Scale(frame, from_=0.0001, to=0.01, variable=lr_var)
        lr_scale.grid(row=2, column=1, sticky=(tk.W, tk.E))
        lr_label = ttk.Label(frame, text=f"{self.config.learning_rate:.5f}")
        lr_label.grid(row=2, column=2)
        lr_scale.config(command=lambda v: lr_label.config(text=f"{float(v):.5f}"))
    
    def on_feature_toggle(self):
        """Handle feature checkbox toggle"""
        # Enable/disable relevant reward sliders
        if 'distance_x' in self.feature_vars:
            distance_active = self.feature_vars['distance_x'].get()
            # Update UI state for distance-related rewards
    
    def submit_config(self):
        """Submit the configuration"""
        # Gather active features
        active_features = {
            feature for feature, var in self.feature_vars.items() 
            if var.get()
        }
        
        # Gather reward weights
        reward_weights = {
            key: var.get() for key, var in self.reward_vars.items()
        }
        
        # Gather learning parameters
        learning_params = {
            key: var.get() for key, var in self.learning_vars.items()
        }
        
        # Close window and return config
        self.root.destroy()
        self.on_submit(active_features, reward_weights, learning_params)
    
    def show(self):
        """Show the UI and wait for user input"""
        self.root.mainloop()