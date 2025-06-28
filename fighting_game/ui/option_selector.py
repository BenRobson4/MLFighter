import random
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import json
from ..config.fighter_manager import FighterManager

from ..config.config_manager import ConfigManager


@dataclass
class AgentOption:
    """Represents one configuration option for an agent"""
    fighter: str
    features: Set[str]
    epsilon: float
    decay: float
    learning_rate: float
    reward_weights: Dict[str, float] = None  # New field
    
    def __post_init__(self):
        """Initialize reward weights if not provided"""
        if self.reward_weights is None:
            self.reward_weights = {
                'health_gain': 1.0,
                'damage_dealt': 1.0,
                'win_bonus': 100.0,
                'loss_penalty': -100.0,
                'distance_bonus': 0.0,
                'aggression_bonus': 0.0,
                'defense_bonus': 0.0
            }
    
    def to_dict(self) -> Dict:
        return {
            'fighter': self.fighter,
            'features': list(self.features),
            'epsilon': self.epsilon,
            'decay': self.decay,
            'learning_rate': self.learning_rate,
            'reward_weights': self.reward_weights
        }
    
    def to_dict(self) -> Dict:
        return {
            'fighter': self.fighter,
            'features': list(self.features),
            'epsilon': self.epsilon,
            'decay': self.decay,
            'learning_rate': self.learning_rate,
            'reward_weights': self.reward_weights
        }


class OptionGenerator:
    """Generates random configuration options"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager 
  
    def generate_options(self, num_options: int = 3) -> List[AgentOption]:
        """Generate random configuration options"""
        options = []

        fighter_manager = FighterManager()
        fighters = fighter_manager.fighter_list()
        
        # Get available features
        tier1_features = self.config.get_features_by_tier("tier1")
        tier2_features = self.config.get_features_by_tier("tier2")
        all_basic_features = tier1_features + tier2_features
        
        # Get parameter ranges
        epsilon_range = self.config.get_parameter_range("epsilon")
        decay_range = self.config.get_parameter_range("decay")
        lr_range = self.config.get_parameter_range("learning_rate")
        
        features_per_option = self.config.config["initial_options"]["features_per_option"]
        
        # Generate unique feature combinations
        used_combinations = set()
        
        for _ in range(num_options):
            attempts = 0
            while attempts < 500:  # Prevent infinite loop
                # Random features
                features = set(random.sample(all_basic_features, 
                                           min(features_per_option, len(all_basic_features))))
                
                # Check if combination is unique
                feature_tuple = tuple(sorted(features))
                if feature_tuple not in used_combinations:
                    used_combinations.add(feature_tuple)
                    # Random character
                    fighter = random.choice(fighters)
                    
                    # Random parameters
                    epsilon = random.uniform(
                        epsilon_range["initial_min"],
                        epsilon_range["initial_max"]
                    )
                    decay = random.uniform(
                        decay_range["initial_min"],
                        decay_range["initial_max"]
                    )
                    learning_rate = random.uniform(
                        lr_range["initial_min"],
                        lr_range["initial_max"]
                    )
                    
                    options.append(AgentOption(
                        fighter=fighter,
                        features=features,
                        epsilon=round(epsilon, 3),
                        decay=round(decay, 4),
                        learning_rate=round(learning_rate, 5),
                        reward_weights=None
                    ))
                    break
                
                attempts += 1
        
        return options


class OptionSelectorUI:
    """UI for selecting from random options and spending tokens on modifications"""
    
    def __init__(self, player_name: str, options: List[AgentOption], 
                 tokens: int, config_manager: ConfigManager, on_complete: callable,
                 current_config: Optional[AgentOption] = None, first_round: bool = True):
        self.player_name = player_name
        self.options = options
        self.tokens = tokens
        self.remaining_tokens = tokens
        self.config = config_manager
        self.on_complete = on_complete
        self.first_round = first_round
        
        # Selected option and modifications
        self.selected_option: Optional[AgentOption] = None
        self.selected_index: Optional[int] = None
        
        # For continuing rounds, use provided config
        if current_config and not first_round:
            self.current_config = AgentOption(
                fighter=current_config.fighter,
                features=set(current_config.features),
                epsilon=current_config.epsilon,
                decay=current_config.decay,
                learning_rate=current_config.learning_rate,
                reward_weights=current_config.reward_weights
            )
        else:
            self.current_config = None
        
        # Available features for unlocking
        self.all_features = set(
            self.config.get_features_by_tier("tier1") + 
            self.config.get_features_by_tier("tier2") +
            self.config.get_features_by_tier("tier3")
        )
        
        # UI setup
        self.root = tk.Tk()
        self.root.title(f"{player_name} - {'Choose' if first_round else 'Modify'} Configuration")
        self.root.geometry("900x700")
        
        self.create_ui()
    
    def create_ui(self):
        """Create the UI"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_text = f"{self.player_name} Configuration"
        if not self.first_round:
            title_text += " - Continuing from Previous Round"
        title = ttk.Label(main_frame, text=title_text, 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Token display
        self.token_label = ttk.Label(main_frame, 
                                    text=f"Tokens: {self.remaining_tokens}/{self.tokens}",
                                    font=('Arial', 12, 'bold'))
        self.token_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        if self.first_round:
            # Phase 1: Option selection (first round only)
            self.create_option_selection(main_frame, row=2)
            
            # Phase 2: Modification (hidden initially)
            self.modification_frame = ttk.Frame(main_frame)
            self.modification_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
            self.modification_frame.grid_remove()
        else:
            # Skip to modification phase for continuing rounds
            self.modification_frame = ttk.Frame(main_frame)
            self.modification_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
            self.create_modification_ui()
            
            # Show current state info
            info_frame = ttk.LabelFrame(main_frame, text="Previous Round Results", padding="10")
            info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(info_frame, 
                     text=f"Epsilon after decay: {self.current_config.epsilon:.3f}",
                     font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
            ttk.Label(info_frame,
                     text=f"Current features: {len(self.current_config.features)}",
                     font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W)
    
    def create_option_selection(self, parent, row):
        """Create option selection UI"""
        frame = ttk.LabelFrame(parent, text="Choose Starting Configuration", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.option_var = tk.IntVar()
        fighter_manager = FighterManager()
        
        for i, option in enumerate(self.options):
            # Fighter
            rb = ttk.Radiobutton(frame, text=f"Fighter: {option.fighter}", 
                               variable=self.option_var, value=i)
            rb.grid(row=i*5, column=0, sticky=tk.W, pady=5)

            fighter_stats = fighter_manager.current_stats(option.fighter)
            fighter_information = "Fighter stats: " + ", ".join(f"{key}: {value}" for key, value in fighter_stats.to_dict().items())
            ttk.Label(frame, text=fighter_information).grid(
                row=i*5+1, column=0, columnspan=2, sticky=tk.W, padx=20)
            # Features
            features_text = "Features: " + ", ".join(sorted(option.features))
            ttk.Label(frame, text=features_text, wraplength=700).grid(
                row=i*5+2, column=0, columnspan=2, sticky=tk.W, padx=20)
            
            # Parameters
            param_text = f"ε: {option.epsilon:.3f}, Decay: {option.decay:.4f}, LR: {option.learning_rate:.5f}"
            ttk.Label(frame, text=param_text).grid(
                row=i*5+3, column=0, columnspan=2, sticky=tk.W, padx=20)
            
            # Separator
            ttk.Separator(frame, orient='horizontal').grid(
                row=i*5+4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Select button
        select_btn = ttk.Button(frame, text="Select This Option", 
                              command=self.select_option)
        select_btn.grid(row=len(self.options)*5, column=0, pady=10)
    
    def select_option(self):
        """Handle option selection"""
        if self.option_var.get() in range(len(self.options)):
            self.selected_index = self.option_var.get()
            self.selected_option = self.options[self.selected_index]
            self.current_config = AgentOption(
                fighter=self.selected_option.fighter,
                features=set(self.selected_option.features),
                epsilon=self.selected_option.epsilon,
                decay=self.selected_option.decay,
                learning_rate=self.selected_option.learning_rate,
                reward_weights=dict(self.selected_option.reward_weights) if self.selected_option.reward_weights else None
            )
            
            # Hide selection, show modification
            for widget in self.root.grid_slaves():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.LabelFrame) and "Choose Starting" in child['text']:
                            child.grid_remove()
            
            self.modification_frame.grid()
            self.create_modification_ui()
    
    def create_modification_ui(self):
        """Create modification UI"""
        # Clear previous content
        for widget in self.modification_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.modification_frame, text="Modify Configuration", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Current configuration display
        config_frame = ttk.LabelFrame(self.modification_frame, text="Current Configuration", padding="5")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.config_labels = {}
        
        # Fighter
        fighter_text = f"Fighter: {self.current_config.fighter}"
        self.config_labels['fighter'] = ttk.Label(config_frame, text=fighter_text)
        self.config_labels['fighter'].grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        # Features
        features_text = "Features: " + ", ".join(sorted(self.current_config.features))
        self.config_labels['features'] = ttk.Label(config_frame, text=features_text, wraplength=700)
        self.config_labels['features'].grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        # Parameters
        self.update_parameter_display(config_frame)
        
        # Modification buttons
        mod_frame = ttk.LabelFrame(self.modification_frame, text="Modifications", padding="10")
        mod_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.create_modification_buttons(mod_frame)
        
        # Finalize button
        finalize_btn = ttk.Button(self.modification_frame, text="Finalize Configuration",
                                command=self.finalize_config)
        finalize_btn.grid(row=3, column=0, columnspan=3, pady=10)
    
    def update_parameter_display(self, parent):
        """Update parameter display"""
        param_text = (f"Epsilon: {self.current_config.epsilon:.3f}, "
                     f"Decay: {self.current_config.decay:.4f}, "
                     f"Learning Rate: {self.current_config.learning_rate:.5f}")
        
        if 'params' in self.config_labels:
            self.config_labels['params'].config(text=param_text)
        else:
            self.config_labels['params'] = ttk.Label(parent, text=param_text)
            self.config_labels['params'].grid(row=2, column=0, columnspan=3, sticky=tk.W)
    
    def create_modification_buttons(self, parent):
        """Create modification buttons"""
        row = 0
        
        # Change fighter button (costs 2 tokens)
        fighter_cost = 2
        ttk.Label(parent, text=f"Change Fighter ({fighter_cost} tokens):").grid(
            row=row, column=0, sticky=tk.W)
        
        fighter_btn = ttk.Button(parent, text="Select Fighter", 
                               command=self.change_fighter)
        fighter_btn.grid(row=row, column=1, padx=5)
        if self.remaining_tokens < fighter_cost:
            fighter_btn.config(state='disabled')
        row += 1
        
        # Unlock feature button
        unlock_cost = self.config.get_cost("unlock_feature")
        ttk.Label(parent, text=f"Unlock Feature ({unlock_cost} tokens):").grid(
            row=row, column=0, sticky=tk.W)
        
        unlock_btn = ttk.Button(parent, text="Choose Feature", 
                              command=self.unlock_feature)
        unlock_btn.grid(row=row, column=1, padx=5)
        if self.remaining_tokens < unlock_cost:
            unlock_btn.config(state='disabled')
        row += 1
        
        # Epsilon modification
        epsilon_cost = self.config.get_cost("modify_epsilon")
        epsilon_delta = self.config.get_modification_delta("epsilon")
        epsilon_range = self.config.get_parameter_range("epsilon")
        
        ttk.Label(parent, text=f"Epsilon ({epsilon_cost} token):").grid(
            row=row, column=0, sticky=tk.W)
        
        eps_minus = ttk.Button(parent, text=f"- {epsilon_delta}", 
                              command=lambda: self.modify_parameter('epsilon', -epsilon_delta))
        eps_minus.grid(row=row, column=1, padx=2)
        if (self.remaining_tokens < epsilon_cost or 
            self.current_config.epsilon - epsilon_delta < epsilon_range["min"]):
            eps_minus.config(state='disabled')
        
        eps_plus = ttk.Button(parent, text=f"+ {epsilon_delta}", 
                            command=lambda: self.modify_parameter('epsilon', epsilon_delta))
        eps_plus.grid(row=row, column=2, padx=2)
        if (self.remaining_tokens < epsilon_cost or 
            self.current_config.epsilon + epsilon_delta > epsilon_range["max"]):
            eps_plus.config(state='disabled')
        row += 1
        
        # Decay modification
        decay_cost = self.config.get_cost("modify_decay")
        decay_delta = self.config.get_modification_delta("decay")
        decay_range = self.config.get_parameter_range("decay")
        
        ttk.Label(parent, text=f"Decay ({decay_cost} token):").grid(
            row=row, column=0, sticky=tk.W)
        
        decay_minus = ttk.Button(parent, text=f"- {decay_delta}", 
                                command=lambda: self.modify_parameter('decay', -decay_delta))
        decay_minus.grid(row=row, column=1, padx=2)
        if (self.remaining_tokens < decay_cost or 
            self.current_config.decay - decay_delta < decay_range["min"]):
            decay_minus.config(state='disabled')
        
        decay_plus = ttk.Button(parent, text=f"+ {decay_delta}", 
                              command=lambda: self.modify_parameter('decay', decay_delta))
        decay_plus.grid(row=row, column=2, padx=2)
        if (self.remaining_tokens < decay_cost or 
            self.current_config.decay + decay_delta > decay_range["max"]):
            decay_plus.config(state='disabled')
        row += 1
        
        # Learning rate modification
        lr_cost = self.config.get_cost("modify_learning_rate")
        lr_delta = self.config.get_modification_delta("learning_rate")
        lr_range = self.config.get_parameter_range("learning_rate")
        
        ttk.Label(parent, text=f"Learning Rate ({lr_cost} token):").grid(
            row=row, column=0, sticky=tk.W)
        
        lr_minus = ttk.Button(parent, text=f"- {lr_delta}", 
                             command=lambda: self.modify_parameter('learning_rate', -lr_delta))
        lr_minus.grid(row=row, column=1, padx=2)
        if (self.remaining_tokens < lr_cost or 
            self.current_config.learning_rate - lr_delta < lr_range["min"]):
            lr_minus.config(state='disabled')
        
        lr_plus = ttk.Button(parent, text=f"+ {lr_delta}", 
                           command=lambda: self.modify_parameter('learning_rate', lr_delta))
        lr_plus.grid(row=row, column=2, padx=2)
        if (self.remaining_tokens < lr_cost or 
            self.current_config.learning_rate + lr_delta > lr_range["max"]):
            lr_plus.config(state='disabled')

        # Add reward weight modification button
        reward_cost = self.config.get_cost("modify_reward_weights")
        ttk.Label(parent, text=f"Modify Reward Weights ({reward_cost} tokens):").grid(
            row=row, column=0, sticky=tk.W)
        
        reward_btn = ttk.Button(parent, text="Adjust Rewards", 
                               command=self.modify_reward_weights)
        reward_btn.grid(row=row, column=1, padx=5)
        if self.remaining_tokens < reward_cost:
            reward_btn.config(state='disabled')
        row += 1
        
        # Show current reward weights summary
        weights_summary = self.get_reward_weights_summary()
        ttk.Label(parent, text=weights_summary, font=('Arial', 9)).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
    
    def get_reward_weights_summary(self) -> str:
        """Get a summary of non-default reward weights"""
        weights = self.current_config.reward_weights
        non_default = []
        
        default_weights = {
            'health_gain': 1.0,
            'damage_dealt': 1.0,
            'win_bonus': 100.0,
            'loss_penalty': -100.0,
            'distance_bonus': 0.0,
            'aggression_bonus': 0.0,
            'defense_bonus': 0.0
        }
        
        for key, value in weights.items():
            if value != default_weights.get(key, 0):
                non_default.append(f"{key}: {value:.1f}")
        
        if non_default:
            return "Modified rewards: " + ", ".join(non_default)
        return "Reward weights: Default"
    
    def modify_reward_weights(self):
        """Show reward weight modification dialog"""
        cost = self.config.get_cost("modify_reward_weight")
        if self.remaining_tokens < cost:
            return
        
        # Load available rewards from config
        with open("fighting_game/config/game_config.json", 'r') as f:
            game_config = json.load(f)
        
        available_rewards = game_config['reward_system']['available_rewards']
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Modify Reward Weights")
        dialog.geometry("600x700")
        
        # Create scrollable frame
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ttk.Label(scrollable_frame, text="Adjust Reward Weights", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        ttk.Label(scrollable_frame, text=f"Cost: {cost} token per modification", 
                font=('Arial', 10)).pack()
        
        # Track modifications
        self.reward_modifications = {}
        weight_vars = {}
        weight_labels = {}
        
        # Create controls for each reward
        for reward_name, reward_info in available_rewards.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            # Reward name and description
            ttk.Label(frame, text=f"{reward_name.replace('_', ' ').title()}:",
                    font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(frame, text=reward_info['description'],
                    font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
            
            # Current value
            current_val = self.current_config.reward_weights.get(reward_name, 0.0)
            
            # Value display and modification buttons
            control_frame = ttk.Frame(frame)
            control_frame.pack(anchor=tk.W, pady=2)
            
            value_label = ttk.Label(control_frame, text=f"{current_val:.1f}", width=8)
            value_label.pack(side=tk.LEFT, padx=5)
            weight_labels[reward_name] = value_label
            
            # Store original value
            weight_vars[reward_name] = {'original': current_val, 'current': current_val}
            
            # Modification buttons
            def modify_weight(name, delta):
                current = weight_vars[name]['current']
                new_val = round(current + delta, 1)
                new_val = max(-100, min(100, new_val))  # Clamp to reasonable range
                
                weight_vars[name]['current'] = new_val
                weight_labels[name].config(text=f"{new_val:.1f}")
                
                # Track if modified
                if new_val != weight_vars[name]['original']:
                    self.reward_modifications[name] = new_val
                elif name in self.reward_modifications:
                    del self.reward_modifications[name]
                
                # Update cost display
                update_cost_display()
            
            ttk.Button(control_frame, text="-10", 
                    command=lambda n=reward_name: modify_weight(n, -10)).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="-1", 
                    command=lambda n=reward_name: modify_weight(n, -1)).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="+1", 
                    command=lambda n=reward_name: modify_weight(n, 1)).pack(side=tk.LEFT, padx=2)
            ttk.Button(control_frame, text="+10", 
                    command=lambda n=reward_name: modify_weight(n, 10)).pack(side=tk.LEFT, padx=2)
            
            # Reset button
            ttk.Button(control_frame, text="Reset",
                    command=lambda n=reward_name: modify_weight(n, 
                        weight_vars[n]['original'] - weight_vars[n]['current'])).pack(side=tk.LEFT, padx=5)
        
        # Cost display
        cost_label = ttk.Label(dialog, text="", font=('Arial', 10, 'bold'))
        cost_label.pack(pady=5)
        
        def update_cost_display():
            num_modifications = len(self.reward_modifications)
            total_cost = num_modifications * cost
            cost_label.config(text=f"Modifications: {num_modifications}, Total Cost: {total_cost} tokens")
            
            # Enable/disable apply button
            if total_cost <= self.remaining_tokens:
                apply_btn.config(state='normal')
            else:
                apply_btn.config(state='disabled')
        
        # Apply button
        def apply_weights():
            total_cost = len(self.reward_modifications) * cost
            if total_cost <= self.remaining_tokens:
                # Apply all modifications
                for reward_name, new_value in self.reward_modifications.items():
                    self.current_config.reward_weights[reward_name] = new_value
                
                self.remaining_tokens -= total_cost
                self.update_display()
                dialog.destroy()
        
        apply_btn = ttk.Button(dialog, text="Apply Changes", command=apply_weights)
        apply_btn.pack(pady=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        update_cost_display()
    
    def unlock_feature(self):
        """Show feature unlock dialog"""
        cost = self.config.get_cost("unlock_feature")
        if self.remaining_tokens < cost:
            return
        
        # Get available features
        available = self.all_features - self.current_config.features
        if not available:
            tk.messagebox.showinfo("No Features", "All features already unlocked!")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Feature to Unlock")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Choose a feature to unlock:", 
                 font=('Arial', 12)).pack(pady=10)
        
        # Feature listbox
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        for feature in sorted(available):
            listbox.insert(tk.END, feature)
        
        def add_feature():
            selection = listbox.curselection()
            if selection:
                feature = listbox.get(selection[0])
                self.current_config.features.add(feature)
                self.remaining_tokens -= cost
                self.update_display()
                dialog.destroy()
        
        ttk.Button(dialog, text="Unlock", command=add_feature).pack(pady=10)
    
    def change_fighter(self):
        """Show fighter change dialog"""
        cost = 2
        if self.remaining_tokens < cost:
            return
        
        # Get available fighters
        fighter_manager = FighterManager()
        available_fighters = fighter_manager.fighter_list()
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Fighter")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Choose a fighter:", 
                 font=('Arial', 12)).pack(pady=10)
        
        # Fighter listbox with stats display
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(frame, height=8)
        listbox.pack(side=tk.LEFT, fill=tk.Y)
        
        # Stats display
        stats_text = tk.Text(frame, width=40, height=8, wrap=tk.WORD)
        stats_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        for fighter in available_fighters:
            listbox.insert(tk.END, fighter)
        
        def on_fighter_select(event):
            selection = listbox.curselection()
            if selection:
                fighter = listbox.get(selection[0])
                stats = fighter_manager.current_stats(fighter)
                stats_info = f"Fighter: {fighter}\n\n"
                stats_info += "\n".join(f"{key.replace('_', ' ').title()}: {value}" 
                                      for key, value in stats.to_dict().items())
                stats_text.delete(1.0, tk.END)
                stats_text.insert(1.0, stats_info)
        
        listbox.bind('<<ListboxSelect>>', on_fighter_select)
        
        def change_fighter_action():
            selection = listbox.curselection()
            if selection:
                fighter = listbox.get(selection[0])
                self.current_config.fighter = fighter
                self.remaining_tokens -= cost
                self.update_display()
                dialog.destroy()
        
        ttk.Button(dialog, text="Select Fighter", command=change_fighter_action).pack(pady=10)
    
    def modify_parameter(self, param: str, delta: float):
        """Modify a parameter"""
        cost = self.config.get_cost(f"modify_{param}")
        if self.remaining_tokens < cost:
            return
        
        # Apply modification
        if param == 'epsilon':
            self.current_config.epsilon = round(
                max(0.0, min(1.0, self.current_config.epsilon + delta)), 3)
        elif param == 'decay':
            self.current_config.decay = round(
                max(0.9, min(1.0, self.current_config.decay + delta)), 4)
        elif param == 'learning_rate':
            self.current_config.learning_rate = round(
                max(0.0001, min(0.01, self.current_config.learning_rate + delta)), 5)
        
        self.remaining_tokens -= cost
        self.update_display()
    
    def update_display(self):
        """Update the display"""
        # Update token display
        self.token_label.config(text=f"Tokens: {self.remaining_tokens}/{self.tokens}")
        
        # Update configuration display
        if 'fighter' in self.config_labels:
            fighter_text = f"Fighter: {self.current_config.fighter}"
            self.config_labels['fighter'].config(text=fighter_text)
        
        features_text = "Features: " + ", ".join(sorted(self.current_config.features))
        self.config_labels['features'].config(text=features_text)
        
        param_text = (f"Epsilon: {self.current_config.epsilon:.3f}, "
                     f"Decay: {self.current_config.decay:.4f}, "
                     f"Learning Rate: {self.current_config.learning_rate:.5f}")
        self.config_labels['params'].config(text=param_text)
        
        # Recreate modification buttons to update states
        for widget in self.modification_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and widget['text'] == "Modifications":
                for child in widget.winfo_children():
                    child.destroy()
                self.create_modification_buttons(widget)
    
    def finalize_config(self):
        """Finalize and return configuration"""
        self.root.destroy()
        self.on_complete(self.current_config)
    
    def show(self):
        """Show the UI"""
        self.root.mainloop()