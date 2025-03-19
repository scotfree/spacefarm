import unittest
from game import Game
from game_objects import Position, Card, Bot, Asset
from game_enums import (
    AssetType, ActionType, Direction, ResourceType,
    ControllerActionType
)

class TestGame(unittest.TestCase):
    def setUp(self):
        # Basic game configuration for testing
        self.config = {
            "map_width": 5,
            "map_height": 5,
            "seedling_maturity_time": 3,
            "new_bot_cost": 10,
            "modify_deck_cost": 5,
            "victory_conditions": {
                "MINERAL": 10,
                "BIOMASS": 10,
                "ENERGY": 10
            },
            "initial_state": "empty",
            "asset_distribution": {
                "ORE": 3,
                "PLANT": 3,
                "COAL": 3
            },
            "controllers": [
                {
                    "resources": {
                        "MINERAL": 0,
                        "BIOMASS": 0,
                        "ENERGY": 10
                    },
                    "bots": [
                        {
                            "x": 2,
                            "y": 2,
                            "deck": [
                                {"type": "MOVE", "parameter": "NORTH"},
                                {"type": "HARVEST", "parameter": "ORE"}
                            ]
                        }
                    ]
                }
            ]
        }
        self.game = Game(self.config)

    def test_game_initialization(self):
        self.assertEqual(self.game.width, 5)
        self.assertEqual(self.game.height, 5)
        self.assertEqual(len(self.game.controllers), 1)
        self.assertEqual(len(self.game.controllers[0].bots), 1)
        self.assertEqual(self.game.day, 0)
        self.assertEqual(self.game.hour, 0)

    def test_bot_movement(self):
        bot = self.game.controllers[0].bots[0]
        original_position = Position(2, 2)
        self.assertEqual(bot.position, original_position)

        # Execute move north
        self.game.execute_bot_action(bot, bot.deck[0])
        expected_position = Position(2, 1)
        self.assertEqual(bot.position, expected_position)

    def test_bot_collision(self):
        # Create two bots in adjacent positions
        controller = self.game.controllers[0]
        
        # Clear all existing bots first
        for y in range(self.game.height):
            for x in range(self.game.width):
                self.game.map[y][x].bots.clear()
        controller.bots.clear()
        
        # Create and position bot1
        bot1 = Bot(Position(2, 2), [Card(ActionType.MOVE, Direction.NORTH)], controller.id)
        controller.bots.append(bot1)
        self.game.map[2][2].bots.add(bot1)
        
        # Create and position bot2
        bot2 = Bot(Position(2, 1), [Card(ActionType.MOVE, Direction.SOUTH)], controller.id)
        controller.bots.append(bot2)
        self.game.map[1][2].bots.add(bot2)
        
        print(f"\nLog (pre): \n{self.game.event_log}")
        # Execute move to cause collision
        self.game.execute_move(bot1, Direction.NORTH)
        print(f"\nLog (post): \n{self.game.event_log}")    

        
        # Both bots should be destroyed
        self.assertEqual(len(controller.bots), 0)
        self.assertEqual(len(self.game.map[2][1].bots), 0)

    def test_resource_harvesting(self):
        controller = self.game.controllers[0]
        bot = controller.bots[0]
        print(f"starting controller resources: {controller.resources}")
        print(f"starting cell resources: {self.game.map[bot.position.y][bot.position.x].assets}")
        # Place ore at bot's position
        self.game.map[bot.position.y][bot.position.x].assets.append(
            Asset(AssetType.ORE, amount=3)
        )

        # Execute harvest action
        harvest_card = Card(ActionType.HARVEST, AssetType.ORE)
        self.game.execute_bot_action(bot, harvest_card)
        print(f"\nLog (post): \n{self.game.event_log}")     
        # Check if resources were added to controller
        self.assertEqual(controller.resources[ResourceType.MINERAL], 3)
        # Check if ore was removed from cell
        self.assertEqual(len(self.game.map[bot.position.y][bot.position.x].assets), 0)

    def test_seedling_maturation(self):
        # Place a seedling
        cell = self.game.map[2][2]
        seedling = Asset(AssetType.ORE_SEEDLING, 1, maturity_time=1)
        cell.assets.append(seedling)

        # Process one turn
        self.game.process_turn()

        # Check if seedling matured into ore
        self.assertEqual(len(cell.assets), 1)
        matured_asset = cell.assets[0]
        self.assertEqual(matured_asset.type, AssetType.ORE)
        self.assertIsNone(matured_asset.maturity_time)
        self.assertGreaterEqual(matured_asset.amount, 1)
        self.assertLessEqual(matured_asset.amount, 5)

    def test_victory_conditions(self):
        controller = self.game.controllers[0]
        
        # Set resources below victory condition
        controller.resources[ResourceType.MINERAL] = 9
        controller.resources[ResourceType.BIOMASS] = 10
        controller.resources[ResourceType.ENERGY] = 10
        
        # Check no victory
        self.assertIsNone(self.game.check_victory())
        
        # Set resources to meet victory conditions
        controller.resources[ResourceType.MINERAL] = 10
        
        # Check victory
        winner = self.game.check_victory()
        self.assertIsNotNone(winner)
        self.assertEqual(winner.id, controller.id)

    def test_process_turn_with_orders(self):
        """Test processing a turn with explicit controller orders."""
        config = {
            'map_width': 10,
            'map_height': 10,
            'seedling_maturity_time': 3,
            'new_bot_cost': 10,
            'modify_deck_cost': 5,
            'victory_conditions': {'MINERAL': 100},
            'initial_state': 'empty',
            'hours_per_day': 24,
            'controllers': [
                {
                    'resources': {'MINERAL': 20, 'BIOMASS': 20, 'ENERGY': 20},
                    'bots': [
                        {
                            'x': 0,
                            'y': 0,
                            'deck': [
                                {'type': 'MOVE', 'parameter': 'EAST'},
                                {'type': 'HARVEST', 'parameter': 'ORE'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        game = Game(config)
        initial_bot_count = len(game.controllers[0].bots)
        initial_energy = game.controllers[0].resources[ResourceType.ENERGY]
        
        # Create turn orders
        turn_orders = [
            {
                'controller_id': 0,
                'action_type': ControllerActionType.TAKE_BOT_ACTIONS,
                'parameters': {'energy_points': 2}
            }
        ]
        
        # Process turn with orders
        game.process_turn(turn_orders)
        
        # Verify energy was spent
        self.assertEqual(
            game.controllers[0].resources[ResourceType.ENERGY],
            initial_energy - 2,
            "Energy points should be deducted"
        )
        
        # Verify hour counter increased
        self.assertEqual(game.hour, 1, "Hour counter should increment")
        self.assertEqual(game.day, 0, "Day should not increment yet")
        
        # Test day increment
        for _ in range(23):  # 23 more hours to complete the day
            game.process_turn(turn_orders)
        
        self.assertEqual(game.hour, 0, "Hour should reset at day end")
        self.assertEqual(game.day, 1, "Day should increment")
        
        # Test invalid controller ID
        invalid_orders = [{
            'controller_id': 99,
            'action_type': ControllerActionType.TAKE_BOT_ACTIONS,
            'parameters': {'energy_points': 1}
        }]
        
        with self.assertRaises(ValueError):
            game.process_turn(invalid_orders)
        
        # Test invalid action type
        invalid_orders = [{
            'controller_id': 0,
            'action_type': "INVALID_ACTION",
            'parameters': {}
        }]
        
        with self.assertRaises(ValueError):
            game.process_turn(invalid_orders)

if __name__ == '__main__':
    unittest.main() 