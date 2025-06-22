from dataclasses import dataclass, asdict

@dataclass
class Purchase:
    """Represents a purchase transaction"""
    item_id: str
    client_id: str
    timestamp: str
    cost: int
    
    def to_dict(self):
        return asdict(self)