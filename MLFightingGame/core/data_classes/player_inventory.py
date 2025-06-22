from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from .weapon import Weapon
from .armour import Armour

@dataclass
class PlayerInventory:
    """Manages player's items and their effects"""
    weapons: List[Weapon] = field(default_factory=list)
    armour: List[Armour] = field(default_factory=list)
    reward_modifiers: Dict[str, List[Dict]] = field(default_factory=dict)
    learning_modifiers: Dict[str, List[Dict]] = field(default_factory=dict)
    features: Set[str] = field(default_factory=set)
    
    def add_weapon(self, weapon: Weapon):
        """Add a weapon to inventory"""
        self.weapons.append(weapon)
        
    def add_armour(self, armour: Armour):
        """Add armour to inventory"""
        self.armour.append(armour)
        
    def add_reward_modifier(self, category: str, modifier: Dict):
        """Add a reward modifier"""
        if category not in self.reward_modifiers:
            self.reward_modifiers[category] = []
        self.reward_modifiers[category].append(modifier)
        
    def add_learning_modifier(self, category: str, modifier: Dict):
        """Add a learning modifier"""
        if category not in self.learning_modifiers:
            self.learning_modifiers[category] = []
        self.learning_modifiers[category].append(modifier)
        
    def add_feature(self, feature_name: str):
        """Unlock a feature"""
        self.features.add(feature_name)
        
    def get_equipped_weapon(self) -> Optional[Weapon]:
        """Get the currently equipped weapon (for now, the last one)"""
        return self.weapons[-1] if self.weapons else None
        
    def get_equipped_armour(self) -> Optional[Armour]:
        """Get the currently equipped armour (for now, the last one)"""
        return self.armour[-1] if self.armour else None
        
    def to_dict(self) -> Dict:
        return {
            "weapons": [w.to_dict() for w in self.weapons],
            "armour": [a.to_dict() for a in self.armour],
            "reward_modifiers": self.reward_modifiers,
            "learning_modifiers": self.learning_modifiers,
            "features": list(self.features)
        }