import json
import os
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Optional, Tuple, Any
from datetime import datetime
import logging
from pathlib import Path

from ..globals.constants import STARTING_GOLD
from ..data_classes import Weapon, Armour, ShopItem, Purchase

from .fighter_option_generator import FighterOptionGenerator

logger = logging.getLogger(__name__)

class ShopManager:
    """Manages shop inventory, purchases, and client gold"""
    
    REFRESH_COST = 10
    ITEMS_PER_SHOP = 5
    
    def __init__(self, starting_gold: int = STARTING_GOLD, items_directory: str = "MLFightingGame/core/shop/items"):
        self.starting_gold = starting_gold
        self.items_directory = items_directory
        
        # Client data
        self.client_gold: Dict[str, int] = {}
        self.client_purchases: Dict[str, List[Purchase]] = {}
        self.purchased_items: Dict[str, Set[str]] = {}
        self.client_current_shop: Dict[str, List[str]] = {}  # Current shop offerings per client
        
        # Shop inventory
        self.all_items: Dict[str, ShopItem] = {}  # item_id -> ShopItem
        self.item_stock: Dict[str, int] = {}  # Current stock levels
        self.category_items: Dict[str, List[str]] = {}  # category -> list of item_ids
        
        # Load all items from JSON files
        self._load_all_items()
        
    def _load_all_items(self):
        """Load all items from JSON files"""
        item_files = {
            "weapons": "weapons.json",
            "armour": "armour.json",
            "reward_modifiers": "reward_modifiers.json",
            "learning_modifiers": "learning_modifiers.json",
            "features": "features.json"
        }
        
        for category, filename in item_files.items():
            filepath = Path(self.items_directory) / filename
            if filepath.exists():
                self._load_items_from_file(filepath, category)
            else:
                logger.warning(f"Item file not found: {filepath}")
                
        logger.info(f"Loaded {len(self.all_items)} total items across {len(self.category_items)} categories")
        
    def _load_items_from_file(self, filepath: Path, category: str):
        """Load items from a specific JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            self.category_items[category] = []
            
            for subcategory, items in data.items():
                for item_key, item_data in items.items():
                    # Generate unique item ID
                    item_id = f"{category}_{subcategory}_{item_key}"
                    
                    # Extract common properties
                    name = item_data.get("name", item_key.replace("_", " ").title())
                    description = item_data.get("description", "")
                    cost = item_data.get("cost", 100)
                    stock = item_data.get("stock", -1)
                    
                    # Create ShopItem
                    shop_item = ShopItem(
                        id=item_id,
                        name=name,
                        description=description,
                        cost=cost,
                        category=category,
                        subcategory=subcategory,
                        stock=stock,
                        properties=item_data
                    )
                    
                    self.all_items[item_id] = shop_item
                    self.category_items[category].append(item_id)
                    
                    # Initialize stock
                    if stock > 0:
                        self.item_stock[item_id] = stock
                        
        except Exception as e:
            logger.error(f"Error loading items from {filepath}: {e}")
            
    def register_client(self, client_id: str):
        """Register a new client with the shop"""
        if client_id not in self.client_gold:
            self.client_gold[client_id] = self.starting_gold
            self.client_purchases[client_id] = []
            self.purchased_items[client_id] = set()
            self.client_current_shop[client_id] = []
            
            # Generate initial shop
            self._generate_shop_for_client(client_id)
            
            logger.info(f"Shop: Registered client {client_id} with {self.starting_gold} gold")
        
    def generate_fighter_options(self, client_id: str, num_options: int = 3) -> List[Dict[str, Any]]:
        """Generate fighter options for initial selection"""        
        options = FighterOptionGenerator.generate_fighter_options(num_options)
        
        # Store options for validation later
        if not hasattr(self, 'client_fighter_options'):
            self.client_fighter_options = {}
        
        self.client_fighter_options[client_id] = {
            opt.option_id: opt for opt in options
        }
        
        return [opt.to_dict() for opt in options]
    
    def process_fighter_selection(self, client_id: str, option_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Process fighter selection and return fighter config"""
        if not hasattr(self, 'client_fighter_options'):
            return False, "No fighter options available", None
        
        if client_id not in self.client_fighter_options:
            return False, "No fighter options for this client", None
        
        if option_id not in self.client_fighter_options[client_id]:
            return False, "Invalid fighter option", None
        
        # Get the selected option
        selected = self.client_fighter_options[client_id][option_id]
        
        # Create player config
        player_config = {
            'fighter_name': selected.fighter_name,
            'starting_gold': self.starting_gold,
            'starting_level': 1,
            'learning_parameters': selected.learning_parameters,
            'initial_feature_mask': selected.initial_feature_mask,
            'starting_items': None
        }
        
        # Clear the options after selection
        del self.client_fighter_options[client_id]
        
        return True, "Fighter selected", player_config
            
    def _get_weighted_item_pool(self, client_id: str) -> List[str]:
        """Create a weighted pool of available items based on stock"""
        weighted_pool = []
        for item_id, item in self.all_items.items():
            # Skip items already purchased (for non-consumables like features)
            if item.category == "features" and item_id in self.purchased_items.get(client_id, set()):
                continue
                
            # Get current stock
            if item.stock >= 0:
                current_stock = self.item_stock.get(item_id, 0)
                if current_stock > 0:
                    # Add item to pool based on stock (weight)
                    weighted_pool.extend([item_id] * current_stock)
            else:
                # Unlimited stock items get weight of 10
                weighted_pool.extend([item_id] * 10)
                
        return weighted_pool
        
    def _generate_shop_for_client(self, client_id: str):
        """Generate a new random shop selection for a client"""
        weighted_pool = self._get_weighted_item_pool(client_id)
        
        if len(weighted_pool) == 0:
            logger.warning(f"No items available for client {client_id}")
            self.client_current_shop[client_id] = []
            return
            
        # Sample unique items (no duplicates in the same shop)
        num_items = min(self.ITEMS_PER_SHOP, len(set(weighted_pool)))
        selected_items = []
        
        # Use weighted random sampling
        pool_copy = weighted_pool.copy()
        for _ in range(num_items):
            if not pool_copy:
                break
                
            chosen = random.choice(pool_copy)
            selected_items.append(chosen)
            
            # Remove all instances of chosen item to avoid duplicates
            pool_copy = [item for item in pool_copy if item != chosen]
            
        self.client_current_shop[client_id] = selected_items
        logger.info(f"Generated shop for {client_id}: {selected_items}")
        
    def refresh_shop(self, client_id: str) -> Tuple[bool, str]:
        """Refresh the shop for a client (costs gold)"""
        if self.client_gold.get(client_id, 0) < self.REFRESH_COST:
            return False, f"Insufficient gold for refresh (need {self.REFRESH_COST})"
            
        # Deduct gold
        self.client_gold[client_id] -= self.REFRESH_COST
        
        # Generate new shop
        self._generate_shop_for_client(client_id)
        
        return True, f"Shop refreshed! (-{self.REFRESH_COST} gold)"
        
    def get_current_shop_items(self, client_id: str) -> List[Dict]:
        """Get the current shop items for a client"""
        if client_id not in self.client_current_shop:
            self._generate_shop_for_client(client_id)
            
        shop_items = []
        for item_id in self.client_current_shop.get(client_id, []):
            if item_id in self.all_items:
                item = self.all_items[item_id]
                item_dict = item.to_dict()
                
                # Only features check for already purchased
                if item.category == "features":
                    item_dict["already_purchased"] = item_id in self.purchased_items.get(client_id, set())
                else:
                    item_dict["already_purchased"] = False
                    
                item_dict["can_afford"] = item.cost <= self.client_gold.get(client_id, 0)
                
                # Add current stock info
                if item.stock >= 0:
                    item_dict["stock_remaining"] = self.item_stock.get(item_id, 0)
                else:
                    item_dict["stock_remaining"] = -1
                    
                shop_items.append(item_dict)
                
        return shop_items
    
    def regenerate_shop(self, client_id: str):
        """Regenerate shop items (free reroll after fights)"""
        # Simply generate a new shop without charging gold
        self._generate_shop_for_client(client_id)
        logger.info(f"Shop regenerated for {client_id} (free post-fight reroll)")
        
    def validate_purchase(self, client_id: str, item_id: str) -> Tuple[bool, str]:
        """Validate if a purchase can be made"""
        # Check if item is in current shop
        if item_id not in self.client_current_shop.get(client_id, []):
            return False, "Item not in current shop"
            
        # Check if item exists
        if item_id not in self.all_items:
            return False, "Item does not exist"
            
        item = self.all_items[item_id]
        
        # Only features are one-time purchases
        if item.category == "features" and item_id in self.purchased_items.get(client_id, set()):
            return False, "Feature already unlocked"
            
        # Check stock
        if item.stock >= 0:
            current_stock = self.item_stock.get(item_id, 0)
            if current_stock <= 0:
                return False, "Item out of stock"
                
        # Check if client can afford it
        client_gold = self.client_gold.get(client_id, 0)
        if client_gold < item.cost:
            return False, f"Insufficient gold (have {client_gold}, need {item.cost})"
            
        return True, "Purchase allowed"
        
    def process_purchase(self, client_id: str, item_id: str) -> Tuple[bool, str, Optional[Purchase]]:
        """Process a purchase request"""
        # Validate first
        is_valid, reason = self.validate_purchase(client_id, item_id)
        if not is_valid:
            return False, reason, None
            
        item = self.all_items[item_id]
        
        # Deduct gold
        self.client_gold[client_id] -= item.cost
        
        # Add to purchased items
        self.purchased_items[client_id].add(item_id)
        
        # Update stock if applicable
        if item.stock >= 0:
            self.item_stock[item_id] -= 1
            logger.info(f"Shop: {item.name} stock reduced to {self.item_stock[item_id]}")
            
        # Create purchase record
        purchase = Purchase(
            item_id=item_id,
            client_id=client_id,
            timestamp=datetime.now().isoformat(),
            cost=item.cost
        )
        self.client_purchases[client_id].append(purchase)
        
        # Remove item from current shop
        self.client_current_shop[client_id].remove(item_id)
        
        logger.info(f"Shop: {client_id} purchased {item.name} for {item.cost} gold")
        
        return True, "Purchase successful", purchase
        
    def get_client_gold(self, client_id: str) -> int:
        """Get client's current gold amount"""
        return self.client_gold.get(client_id, 0)
        
    def get_purchase_summary(self, client_id: str) -> Dict:
        """Get a summary of client's shop activity"""
        purchases = self.client_purchases.get(client_id, [])
        return {
            "total_purchases": len(purchases),
            "total_spent": sum(p.cost for p in purchases),
            "items_owned": list(self.purchased_items.get(client_id, set())),
            "remaining_gold": self.get_client_gold(client_id),
            "purchase_history": [p.to_dict() for p in purchases]
        }
        
    def add_gold_to_client(self, client_id: str, amount: int):
        """Add gold to a client's account"""
        if client_id in self.client_gold:
            self.client_gold[client_id] += amount
            logger.info(f"Shop: Added {amount} gold to {client_id}. New total: {self.client_gold[client_id]}")