from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional
from .weapon import Weapon
from .armour import Armour

@dataclass
class PlayerInventory:
    """Manages player's inventory with quantity tracking"""
    weapons: List[Weapon] = field(default_factory=list)  # All owned weapons
    armour: List[Armour] = field(default_factory=list)   # All owned armour
    features: Set[str] = field(default_factory=set)      # Unlocked features (no duplicates)
    reward_modifiers: Dict[str, List[Dict]] = field(default_factory=dict)
    learning_modifiers: Dict[str, List[Dict]] = field(default_factory=dict)
    
    # Remove these old fields
    # equipped_weapon_index: Optional[int] = None  # Index in weapons list
    # equipped_armour_index: Optional[int] = None  # Index in armour list
    
    def add_weapon(self, weapon: Weapon):
        """Add a weapon and auto-equip it (most recent)"""
        # Unequip all other weapons
        for w in self.weapons:
            w.equipped = False
        
        # Add new weapon as equipped
        weapon.equipped = True
        self.weapons.append(weapon)
        
    def add_armour(self, armour: Armour):
        """Add armour and auto-equip it (most recent)"""
        # Unequip all other armour
        for a in self.armour:
            a.equipped = False
            
        # Add new armour as equipped
        armour.equipped = True
        self.armour.append(armour)
        
    def get_equipped_weapon(self) -> Optional[Weapon]:
        """Get currently equipped weapon"""
        for weapon in self.weapons:
            if weapon.equipped:
                return weapon
        return None
        
    def get_equipped_armour(self) -> Optional[Armour]:
        """Get currently equipped armour"""
        for armour in self.armour:
            if armour.equipped:
                return armour
        return None
    
    def equip_weapon(self, weapon_index: int) -> bool:
        """Equip a specific weapon by index"""
        if 0 <= weapon_index < len(self.weapons):
            # Unequip all weapons
            for w in self.weapons:
                w.equipped = False
            # Equip the selected weapon
            self.weapons[weapon_index].equipped = True
            return True
        return False
    
    def equip_armour(self, armour_index: int) -> bool:
        """Equip a specific armour by index"""
        if 0 <= armour_index < len(self.armour):
            # Unequip all armour
            for a in self.armour:
                a.equipped = False
            # Equip the selected armour
            self.armour[armour_index].equipped = True
            return True
        return False
    
    def add_feature(self, feature_name: str):
        """Add a feature (only once)"""
        self.features.add(feature_name)
        
    def add_reward_modifier(self, category: str, modifier: Dict):
        """Add a reward modifier (stacks with existing)"""
        if category not in self.reward_modifiers:
            self.reward_modifiers[category] = []
        self.reward_modifiers[category].append(modifier)
        
    def add_learning_modifier(self, category: str, modifier: Dict):
        """Add a learning modifier (stacks with existing)"""
        if category not in self.learning_modifiers:
            self.learning_modifiers[category] = []
        self.learning_modifiers[category].append(modifier)
    
    def get_weapon_count(self) -> Dict[str, int]:
        """Get count of each weapon type"""
        counts = {}
        for weapon in self.weapons:
            counts[weapon.name] = counts.get(weapon.name, 0) + 1
        return counts
    
    def get_armour_count(self) -> Dict[str, int]:
        """Get count of each armour type"""
        counts = {}
        for armour in self.armour:
            counts[armour.name] = counts.get(armour.name, 0) + 1
        return counts
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving"""
        return {
            "weapons": [asdict(w) for w in self.weapons],
            "armour": [asdict(a) for a in self.armour],
            "features": list(self.features),
            "reward_modifiers": self.reward_modifiers,
            "learning_modifiers": self.learning_modifiers,
            # No longer need equipped indices
            "weapon_counts": self.get_weapon_count(),
            "armour_counts": self.get_armour_count()
        }