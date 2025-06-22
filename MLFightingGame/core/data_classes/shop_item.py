from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ShopItem:
    """Generic shop item that can represent any purchasable item"""
    id: str
    name: str
    description: str
    cost: int
    category: str  # weapons, armour, reward_modifiers, etc.
    subcategory: str  # sword, dagger, epsilon, etc.
    stock: int = -1
    properties: Dict[str, Any] = None  # Store all item-specific properties
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "category": self.category,
            "subcategory": self.subcategory,
            "stock": self.stock,
            "properties": self.properties or {}
        }

