from game_enums import AssetType, ActionType, Direction, ResourceType

config = {
    # Map dimensions
    'map_width': 5,
    'map_height': 5,
    
    # Game parameters
    'seedling_maturity_time': 5,
    'new_bot_cost': 20,
    'modify_deck_cost': 2,
    
    # Victory conditions
    'victory_conditions': {
        ResourceType.BIOMASS: 20
    },
    
    # Initial state - uniform distribution
    'initial_state': 'uniform',
    'asset_distribution': {
        AssetType.ORE: 2,
        AssetType.PLANT: 2,
        AssetType.COAL: 2
    },
    
    # Controllers
    'controllers': [
        {
            'id': 'player1',
            'resources': {
                ResourceType.MINERAL: 10,
                ResourceType.BIOMASS: 10,
                ResourceType.ENERGY: 10
            },
            'bots': [
                {
                    'x': 2,  # Center of the 5x5 grid
                    'y': 2,
                    'deck': [
                        {'type': ActionType.MOVE, 'parameter': Direction.NORTH},
                        {'type': ActionType.MOVE, 'parameter': Direction.SOUTH},
                        {'type': ActionType.MOVE, 'parameter': Direction.EAST},
                        {'type': ActionType.MOVE, 'parameter': Direction.WEST},
                        {'type': ActionType.HARVEST, 'parameter': AssetType.PLANT},
                        {'type': ActionType.PLANT, 'parameter': AssetType.PLANT},
                        {'type': ActionType.HARVEST, 'parameter': AssetType.ORE},
                        {'type': ActionType.HARVEST, 'parameter': AssetType.COAL}
                    ]
                }
            ]
        }
    ]
} 