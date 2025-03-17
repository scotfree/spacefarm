import unittest
from game import Game
from game_interface import GameInterface
from game_objects import Position, Asset, Card, Bot
from game_enums import AssetType, ActionType, Direction, ResourceType

class TestGameInterface(unittest.TestCase):
    def setUp(self):
        # Basic game configuration for testing
        self.config = {
            "map_width": 5,  # Changed from 3 to meet minimum requirement
            "map_height": 5,  # Changed from 3 to meet minimum requirement
            "seedling_maturity_time": 3,
            "new_bot_cost": 10,
            "modify_deck_cost": 5,
            "victory_conditions": {
                "MINERAL": 10,
                "BIOMASS": 10,
                "ENERGY": 10
            },
            "initial_state": "uniform",
            "asset_distribution": {
                "ORE": 2,
                "PLANT": 2,
                "COAL": 2,
                "ORE_SEEDLING": 1,
                "PLANT_SEEDLING": 1,
                "COAL_SEEDLING": 1
            },
            "controllers": [
                {
                    "resources": {
                        "MINERAL": 5,
                        "BIOMASS": 3,
                        "ENERGY": 10
                    },
                    "bots": [
                        {
                            "x": 2,
                            "y": 2,
                            "deck": [
                                {"type": "MOVE", "parameter": "RANDOM"},
                                {"type": "HARVEST", "parameter": "ORE"}
                            ]
                        }
                    ]
                }
            ]
        }
        self.game = Game(self.config)

    def test_grid_generation_basic_structure(self):
        html = GameInterface.generate_html_grid(self.game)
        
        # Check basic HTML structure
        self.assertIn('<div class="game-grid">', html)
        self.assertIn('</div>', html)
        self.assertIn('<style>', html)
        
        # Check grid dimensions (5x5 = 25 cells)
        cell_count = html.count('<div class="cell"')
        self.assertEqual(cell_count, 25)
        
        # Check coordinates are present
        self.assertIn('(0,0)', html)
        self.assertIn('(4,4)', html)

    def test_grid_cell_contents(self):
        # Place a test asset and check its representation
        cell = self.game.map[1][1]
        cell.assets.clear()
        cell.assets.append(Asset(AssetType.ORE, 3))
        
        html = GameInterface.generate_html_grid(self.game)
        
        # Check asset label
        self.assertIn('ORE×3', html)
        
        # Check cell color
        self.assertIn(GameInterface.ASSET_COLORS[AssetType.ORE], html)

    def test_seedling_display(self):
        # Place a seedling and check its representation
        cell = self.game.map[1][1]
        cell.assets.clear()
        cell.assets.append(Asset(AssetType.ORE_SEEDLING, 1, maturity_time=3))
        
        html = GameInterface.generate_html_grid(self.game)
        
        # Check seedling label with maturity time
        self.assertIn('ORS(3)', html)
        
        # Check seedling color
        self.assertIn(GameInterface.ASSET_COLORS[AssetType.ORE_SEEDLING], html)

    def test_bot_display(self):
        # Clear all existing bots from the game
        for row in self.game.map:
            for cell in row:
                cell.bots.clear()
        
        # Clear controller's bots
        self.game.controllers[0].bots.clear()
        
        # Create position and bots
        pos = Position(2, 2)
        bot1 = Bot(position=pos, deck=[], controller_id=0)
        bot2 = Bot(position=pos, deck=[], controller_id=0)
        
        # Add bots to controller
        self.game.controllers[0].bots.extend([bot1, bot2])
        
        # Add bots to map cell
        cell = self.game.map[pos.y][pos.x]
        cell.assets.clear()  # Clear any existing assets for clean test
        cell.bots.clear()    # Ensure cell is empty
        cell.bots.add(bot1)  # Add bots one at a time to ensure proper set behavior
        cell.bots.add(bot2)
        
        # Debug output
        print(f"\nCell bots: {len(cell.bots)}")
        print(f"Controller bots: {len(self.game.controllers[0].bots)}")
        print(f"Bot positions: {[b.position for b in cell.bots]}")
        
        # Generate HTML and verify
        html = GameInterface.generate_html_grid(self.game)
        self.assertIn('C0', html)  # Should show 2 bots from controller 0

    def test_game_state_summary(self):
        summary = GameInterface.get_game_state_summary(self.game)
        
        # Check turn counter
        self.assertIn('Turn: 0', summary
                      
                      )
        
        # Check resource display
        self.assertIn('MINERAL: 5', summary)
        self.assertIn('BIOMASS: 3', summary)
        self.assertIn('ENERGY: 10', summary)
        
        # Check victory conditions
        self.assertIn('Victory Conditions:', summary)
        self.assertIn('MINERAL: 10', summary)

    def test_deck_display(self):
        summary = GameInterface.get_game_state_summary(self.game)
        
        # Check deck contents
        self.assertIn('M?', summary)  # Random move
        self.assertIn('HO', summary)  # Harvest ore

    def test_event_log(self):
        # Add some test events
        self.game.log_event("Test event 1")
        self.game.log_event("Test event 2")
        
        summary = GameInterface.get_game_state_summary(self.game)
        
        # Check event log display
        self.assertIn('Event Log:', summary)
        self.assertIn('Test event 1', summary)
        self.assertIn('Test event 2', summary)

    def test_multiple_assets_same_cell(self):
        cell = self.game.map[1][1]
        cell.assets.clear()
        cell.assets.extend([
            Asset(AssetType.ORE, 2),
            Asset(AssetType.PLANT, 1),
            Asset(AssetType.ORE_SEEDLING, 1, maturity_time=3)
        ])
        
        html = GameInterface.generate_html_grid(self.game)
        
        # Check all assets are displayed
        self.assertIn('ORE×2', html)
        self.assertIn('PLT', html)
        self.assertIn('ORS(3)', html)

    def test_empty_cell_display(self):
        # Clear a cell and check its representation
        cell = self.game.map[0][0]
        cell.assets.clear()
        cell.bots.clear()
        
        html = GameInterface.generate_html_grid(self.game)
        
        # Check empty cell color
        self.assertIn('#9BA2A7', html)  # Default color for empty cells

if __name__ == '__main__':
    unittest.main() 