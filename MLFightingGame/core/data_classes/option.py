from dataclasses import dataclass, asdict

@dataclass
class Option:
    """Represents a purchasable item"""
    id: str
    name: str
    description: str
    cost: int = 0
    stock: int = -1  # -1 means unlimited stock
    available: bool = True
    
    def to_dict(self):
        return asdict(self)