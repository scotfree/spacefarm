from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple, Union
from game_enums import Position, AssetType, ActionType, Direction, ResourceType

@dataclass
class Asset:
    type: AssetType
    amount: int
    maturity_time: Optional[int] = None  # None for mature assets

@dataclass(frozen=True)  # Make Card immutable and automatically add __hash__
class Card:
    action_type: ActionType
    parameter: Union[Direction, AssetType]  # Direction for MOVE, AssetType for HARVEST/PLANT

@dataclass
class Bot:
    position: Position
    deck: List[Card]
    controller_id: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bot):
            return NotImplemented
        return (self.position == other.position and 
                self.controller_id == other.controller_id)

    def __hash__(self) -> int:
        return hash((self.position, self.controller_id))

class Cell:
    def __init__(self):
        self.assets: List[Asset] = []
        self.bots: Set[Bot] = set()

class Controller:
    def __init__(self, id: int):
        self.id = id
        self.bots: List[Bot] = []
        self.resources = {
            ResourceType.MINERAL: 0,
            ResourceType.BIOMASS: 0,
            ResourceType.ENERGY: 0
        }
        self.starting_position = Position(0, 0)  # Default starting position

    def get_total_resources(self) -> int:
        """Get the total amount of resources this controller has."""
        return sum(self.resources.values())

    def deduct_resources(self, amount: int) -> None:
        """Deduct resources from the controller's total."""
        # Deduct proportionally from each resource type
        total = self.get_total_resources()
        if total < amount:
            raise ValueError("Insufficient resources")
        
        for resource_type in self.resources:
            proportion = self.resources[resource_type] / total
            deduction = int(amount * proportion)
            self.resources[resource_type] -= deduction 