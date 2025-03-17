import unittest
from game_objects import Position, Asset, Card, Bot, Cell, Controller
from game_enums import AssetType, ActionType, Direction, ResourceType

class TestPosition(unittest.TestCase):
    def test_position_addition(self):
        pos1 = Position(1, 2)
        pos2 = Position(3, -1)
        result = pos1 + pos2
        self.assertEqual(result.x, 4)
        self.assertEqual(result.y, 1)

    def test_position_equality(self):
        pos1 = Position(1, 2)
        pos2 = Position(1, 2)
        pos3 = Position(2, 1)
        self.assertEqual(pos1, pos2)
        self.assertNotEqual(pos1, pos3)

class TestAsset(unittest.TestCase):
    def test_asset_creation(self):
        asset = Asset(AssetType.ORE, 5)
        self.assertEqual(asset.type, AssetType.ORE)
        self.assertEqual(asset.amount, 5)
        self.assertIsNone(asset.maturity_time)

    def test_seedling_creation(self):
        seedling = Asset(AssetType.ORE_SEEDLING, 1, maturity_time=3)
        self.assertEqual(seedling.type, AssetType.ORE_SEEDLING)
        self.assertEqual(seedling.amount, 1)
        self.assertEqual(seedling.maturity_time, 3)

class TestBot(unittest.TestCase):
    def test_bot_creation(self):
        pos = Position(2, 3)
        deck = [
            Card(ActionType.MOVE, Direction.NORTH),
            Card(ActionType.HARVEST, AssetType.ORE)
        ]
        bot = Bot(pos, deck, controller_id=0)
        
        self.assertEqual(bot.position, pos)
        self.assertEqual(len(bot.deck), 2)
        self.assertEqual(bot.controller_id, 0)

    def test_bot_deck_operations(self):
        pos = Position(0, 0)
        deck = [
            Card(ActionType.MOVE, Direction.NORTH),
            Card(ActionType.MOVE, Direction.SOUTH)
        ]
        bot = Bot(pos, deck, controller_id=0)
        
        # Test deck rotation
        first_card = bot.deck[0]
        bot.deck = bot.deck[1:] + [first_card]
        self.assertEqual(bot.deck[-1], first_card)
        self.assertEqual(len(bot.deck), 2)

class TestController(unittest.TestCase):
    def test_controller_creation(self):
        controller = Controller(0)
        self.assertEqual(controller.id, 0)
        self.assertEqual(len(controller.bots), 0)
        self.assertEqual(len(controller.resources), len(ResourceType))
        
        # Check that all resource types are initialized to 0
        for resource_type in ResourceType:
            self.assertEqual(controller.resources[resource_type], 0)

    def test_controller_resource_management(self):
        controller = Controller(0)
        controller.resources[ResourceType.MINERAL] = 10
        
        self.assertEqual(controller.resources[ResourceType.MINERAL], 10)
        self.assertEqual(controller.resources[ResourceType.ENERGY], 0)

class TestCell(unittest.TestCase):
    def test_cell_creation(self):
        cell = Cell()
        self.assertEqual(len(cell.assets), 0)
        self.assertEqual(len(cell.bots), 0)

    def test_cell_asset_management(self):
        cell = Cell()
        asset = Asset(AssetType.ORE, 3)
        cell.assets.append(asset)
        
        self.assertEqual(len(cell.assets), 1)
        self.assertEqual(cell.assets[0].type, AssetType.ORE)
        self.assertEqual(cell.assets[0].amount, 3)

    def test_cell_bot_management(self):
        cell = Cell()
        bot = Bot(Position(0, 0), [], controller_id=0)
        cell.bots.add(bot)
        
        self.assertEqual(len(cell.bots), 1)
        self.assertTrue(bot in cell.bots)

if __name__ == '__main__':
    unittest.main() 