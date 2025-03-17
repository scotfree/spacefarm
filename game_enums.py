from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, Union

@dataclass(frozen=True)
class Position:
    x: int
    y: int
    
    def __add__(self, other: Union['Position', Tuple[int, int]]) -> 'Position':
        if isinstance(other, tuple):
            return Position(self.x + other[0], self.y + other[1])
        elif isinstance(other, Position):
            return Position(self.x + other.x, self.y + other.y)
        raise TypeError(f"Cannot add Position with {type(other)}")

class Direction(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()
    RANDOM = auto()

class ActionType(Enum):
    MOVE = auto()
    HARVEST = auto()
    PLANT = auto()

class AssetType(Enum):
    ORE = auto()
    PLANT = auto()
    COAL = auto()
    ORE_SEEDLING = auto()
    PLANT_SEEDLING = auto()
    COAL_SEEDLING = auto()

class ResourceType(Enum):
    MINERAL = auto()
    BIOMASS = auto()
    ENERGY = auto()

class ControllerActionType(Enum):
    """Types of actions a controller can take during their turn"""
    TAKE_BOT_ACTIONS = "take_bot_actions"
    MODIFY_DECK = "modify_deck"
    CREATE_BOT = "create_bot"

# Direction vectors for movement
DIRECTION_VECTORS = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0)
}

# Mapping from assets to resources when harvesting
ASSET_TO_RESOURCE = {
    AssetType.ORE: ResourceType.MINERAL,
    AssetType.PLANT: ResourceType.BIOMASS,
    AssetType.COAL: ResourceType.ENERGY
}

# Mapping from seedlings to mature assets
SEEDLING_TO_ASSET = {
    AssetType.ORE_SEEDLING: AssetType.ORE,
    AssetType.PLANT_SEEDLING: AssetType.PLANT,
    AssetType.COAL_SEEDLING: AssetType.COAL
} 