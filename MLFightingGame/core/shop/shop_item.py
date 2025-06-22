from items import ItemCategory
from ..data_classes import Weapon, Armour

class ShopItem:

    def __init__(self, category: ItemCategory, id: int):
        
        self.id = id
        item_info = self.get_item_info(category, id)
        self.name = item_info['name']
        self.description = item_info['description']
        self.cost = item_info['cost']
        self.category = category
        self.rarity = item_info['rarity']
        # TODO: Implement a get stats method, possible using case matching to generate a different stats object based on
        # the item type. I think I need to keep the weapon and armour dataclasses to work with the player class as that
        # uses those features heavily but the other ones - features, learning_params, and reward_modifiers can return just
        # dictionaries here I think. All these different bits of information will be stored in their respective jsons.