import random
from typing import List, Dict, Optional, Set, Tuple, Union
from game_objects import *
from game_enums import (
    Direction, ActionType, AssetType, ResourceType, ControllerActionType,
    DIRECTION_VECTORS, ASSET_TO_RESOURCE, SEEDLING_TO_ASSET
)
MAIN_HELP = """
Your space ship, the "Stardew Valley", has crashed!
You are able to stay alive inside the wreck mostly by sleeping in your suspended animation pod to reduce resource usage.
To gather enough resources to survice and eventually repair your ship, you;ll need to gather and grow from the outside world which you cannot visit.
Luckily, you have built a Bot which can take your orders in the outside world and perform your tasks.
You will need to give it its orders then return to sleep while it performs them.
The longer you can let it run while you sleep the more efficient your operation will be, but the harder it will be adapt to any changes or challenges to the assuptions underlying your orders.

Your primary control is how to spend the hours of your days. While you sleep your bots will perform your given tasks. Reprogramming the bots or building new ones will require you to be awake, which consumes your precious biomass.

Biomass: perforrm waking tasks
Energy: perform bot actions and tasks
Metal: build new machinery and components

Controls:
RUN: let N hours pass, consuming no biomass while bots work
EDIT: reconfigure your bots, cosuming biomass
NEW: Create new bot out of metal

Each scenatior will have a set of goals to be accomplished - generally needed amounts of resources.

"""


class Game:
    def __init__(self, config: dict):
        self.validate_config(config)
        
        self.width = config['map_width']
        self.height = config['map_height']
        self.map = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.controllers: List[Controller] = []
        self.day = 0
        self.hour = 0
        self.hours_per_day = config.get('hours_per_day', 24)
        self.seedling_maturity_time = config['seedling_maturity_time']
        
        # Action hour costs
        self.hour_costs = {
            'bot_action': 1,
            'modify_deck': 1,
            'new_bot': 6
        }
        
        # Store costs from config
        self.costs = {
            'new_bot': config['new_bot_cost'],
            'modify_deck': config['modify_deck_cost'],
        }
        
        self.victory_conditions = config['victory_conditions']
        self.state = 'active'
        self.victors = []
        # Add event log
        self.event_log: List[Dict[str, Union[int, str]]] = []
        
        self.setup_initial_state(config)

    def validate_config(self, config: dict) -> None:
        required_fields = {
            'map_width': (5, 1000),
            'map_height': (5, 1000),
            'seedling_maturity_time': (1, 100),
            'new_bot_cost': (1, 1000),
            'modify_deck_cost': (1, 1000),
            'victory_conditions': None,
            'initial_state': None,
            'hours_per_day': (1, 48)
        }
        
        for field, bounds in required_fields.items():
            if field not in config and field != 'hours_per_day':
                raise ValueError(f"Missing required config field: {field}")
            if bounds and field in config:
                value = config[field]
                if not isinstance(value, int) or value < bounds[0] or value > bounds[1]:
                    raise ValueError(f"{field} must be between {bounds[0]} and {bounds[1]}")

    def setup_initial_state(self, config: dict) -> None:
        # Initialize controllers and their bots
        for controller_data in config['controllers']:
            controller = Controller(len(self.controllers))
            self.controllers.append(controller)
            
            # Set initial resources
            for resource_name, amount in controller_data['resources'].items():
                controller.resources[ResourceType[resource_name]] = amount
            
            # Set up bots
            for bot_data in controller_data['bots']:
                pos = Position(bot_data['x'], bot_data['y'])
                # Convert string actions to enum types
                deck = []
                for action in bot_data['deck']:
                    action_type = ActionType[action['type']]
                    # Parameter could be either Direction or AssetType
                    if action_type == ActionType.MOVE:
                        parameter = Direction[action['parameter']]
                    else:  # HARVEST or PLANT
                        parameter = AssetType[action['parameter']]
                    deck.append(Card(action_type, parameter))
                
                bot = Bot(pos, deck, controller.id)
                controller.bots.append(bot)
                self.map[pos.y][pos.x].bots.add(bot)

        # Set up initial assets
        if config['initial_state'] == 'uniform':
            distribution = {
                AssetType[asset_type]: count 
                for asset_type, count in config['asset_distribution'].items()
            }
            self.generate_uniform_assets(distribution)
        elif config['initial_state'] == 'empty':
            # No assets are added to the map
            pass
        else:
            for asset_data in config['initial_state']:
                asset = Asset(
                    AssetType[asset_data['type']], 
                    asset_data['amount']
                )
                pos = Position(asset_data['x'], asset_data['y'])
                self.map[pos.y][pos.x].assets.append(asset)

        # Convert victory conditions
        self.victory_conditions = {
            ResourceType[resource_type]: amount 
            for resource_type, amount in config['victory_conditions'].items()
        }

    def process_turn(self, turn_orders: Optional[List[Dict]] = None) -> None:
        """Process a single game turn with optional controller orders.
        
        Args:
            turn_orders: List of dictionaries containing controller orders.
                Each dictionary should have:
                - controller_id: ID of the controller
                - action_type: ControllerActionType enum value
                - parameters: Dict of parameters needed for the action
        """
        if turn_orders:
            # Validate orders
            for order in turn_orders:
                controller_id = order.get('controller_id')
                action_type = order.get('action_type')
                parameters = order.get('parameters', {})

                # Validate controller exists
                if controller_id is None or controller_id >= len(self.controllers):
                    raise ValueError(f"Invalid controller_id: {controller_id}")

                # Validate action type
                if not isinstance(action_type, ControllerActionType):
                    raise ValueError(f"Invalid action_type: {action_type}")

                # Process the controller action
                controller = self.controllers[controller_id]
                self.process_controller_action(controller, action_type, parameters)

        # Mature seedlings
        self.mature_seedlings()
        
        # Increment hour counter
        # self.hour += 1
        
        # Check if day is complete
        if self.hour >= self.hours_per_day:
            self.hour = 0
            self.day += 1
        
        for controller in self.controllers[:]:  # Copy list to allow removal during iteration
            if controller.resources[ResourceType.ENERGY] <= 0:
                print("GAME OVER")
                self.log_event(f"Controller {controller.id} has no energy left and is eliminated")
                self.eliminate_controller(controller)
                continue
            
            # This would be called by the game interface with the controller's chosen action
            # action = get_controller_action(controller)  # Not implemented here
            # self.process_controller_turn(controller, action)
        
        # Check for victory after all controllers have moved
        winner = self.check_victory()
        if winner:
            return winner

    def eliminate_controller(self, controller: Controller) -> None:
        """Remove a controller and destroy all their bots"""
        for bot in controller.bots[:]:  # Copy list to allow modification
            self.destroy_bot(bot)
        self.controllers.remove(controller)

    def destroy_bot(self, bot: Bot) -> None:
        """Remove a bot from the game."""
        # First remove from controller's bot list
        controller = self.controllers[bot.controller_id]
        # Create a new list without the bot, using identity comparison
        new_bots = []
        for b in controller.bots:
            if b is not bot:  # Use identity comparison
                new_bots.append(b)
        controller.bots = new_bots
        
        # Then remove from map cell
        cell = self.map[bot.position.y][bot.position.x]
        cell.bots.discard(bot)
        
        self.log_event(f"Bot {bot.controller_id} destroyed at ({bot.position.x}, {bot.position.y})")

    def process_bot_actions(self, controller: Controller, energy_spent: int) -> None:
        """Process random bot actions for a controller"""
        if energy_spent > controller.resources[ResourceType.ENERGY]:
            raise ValueError("Not enough energy")
        
        controller.resources[ResourceType.ENERGY] -= energy_spent
        
        for _ in range(energy_spent):
            if not controller.bots:
                break
            bot = random.choice(controller.bots)
            # Execute action using top card
            card = bot.deck[0]
            self.execute_bot_action(bot, card)
            # Move the card to the bottom of the deck
            bot.deck = bot.deck[1:] + [card]

    def execute_bot_action(self, bot: Bot, card: Card) -> None:
        """Execute a single bot action"""
        if card.action_type == ActionType.MOVE:
            self.execute_move(bot, card.parameter)
        elif card.action_type == ActionType.HARVEST:
            self.execute_harvest(bot, card.parameter)
        elif card.action_type == ActionType.PLANT:
            self.execute_plant(bot, card.parameter)

    def execute_move(self, bot: Bot, direction: Direction) -> bool:
        """Execute a move action for a bot."""
        if direction == Direction.RANDOM:
            direction = random.choice([Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST])
        
        old_pos = bot.position
        new_pos = old_pos + DIRECTION_VECTORS[direction]
        # print(f"Move from ({old_pos.x}, {old_pos.y}) to ({new_pos.x}, {new_pos.y}) by bot {bot}")

        self.log_event(f"Move from ({old_pos.x}, {old_pos.y}) to ({new_pos.x}, {new_pos.y}) by bot {bot}")

        # Check if move is valid
        if not self.is_valid_position(new_pos):
            print("Invalid position!")
            return False
        
        # Get cells
        old_cell = self.map[old_pos.y][old_pos.x]
        new_cell = self.map[new_pos.y][new_pos.x]
        # print(f"OLD Cell bots: {old_cell.bots}")
        # print(f"NEW Cell bots: {new_cell.bots}")

        # Check for collision
        if not new_cell.bots:
            pass
            # print(f"NO collicion yay. {old_pos} {new_pos}\n{bot}")
            # print(f"Controller bots: {self.controllers[bot.controller_id].bots}")
            #print(f"OLD Cell bots: {old_cell.bots}")
            #print(f"NEW Cell bots: {new_cell.bots}")

        else:
            # Log collision event
            #print(f"Collision detected at ({new_pos.x}, {new_pos.y})")
            self.log_event(f"Collision detected at ({new_pos.x}, {new_pos.y})")
            
            # Collect all bots to be removed (both moving and colliding)
            bots_to_remove = set()
            bots_to_remove.add(bot)
            bots_to_remove.update(new_cell.bots)
            
            # Remove all bots from their cells first
            old_cell.bots.discard(bot)
            new_cell.bots.clear()
            
            # Remove all bots from their controllers
            for bot_to_remove in bots_to_remove:
                controller = self.controllers[bot_to_remove.controller_id]
                # Create new list without the bot
                controller.bots = [b for b in controller.bots if id(b) != id(bot_to_remove)]
                self.log_event(f"Bot {bot_to_remove.controller_id} destroyed at ({bot_to_remove.position.x}, {bot_to_remove.position.y})")
            
            return True
        
        # No collision, proceed with move
        old_cell.bots.discard(bot)
        bot.position = new_pos
        new_cell.bots.add(bot)
        return True

    def execute_harvest(self, bot: Bot, asset_type: AssetType) -> bool:
        """Harvest an asset at the bot's location."""
        cell = self.map[bot.position.y][bot.position.x]
        
        # Find matching mature asset
        for i, asset in enumerate(cell.assets):
            if asset.type == asset_type and asset.maturity_time is None:
                # Convert asset to resource and add to controller
                resource_type = ASSET_TO_RESOURCE[asset_type]
                self.controllers[bot.controller_id].resources[resource_type] += asset.amount
                
                # Remove the harvested asset
                cell.assets.pop(i)
                
                self.log_event(f"Bot {bot.controller_id} harvested {asset.amount} {asset_type.name} at ({bot.position.x}, {bot.position.y})")
                return True
        
        self.log_event(f"Bot {bot.controller_id} failed to harvest {asset_type.name} at ({bot.position.x}, {bot.position.y})")
        return False

    def execute_plant(self, bot: Bot, asset_type: AssetType) -> None:
        """Plant a seedling at the bot's location"""
        cell = self.map[bot.position.y][bot.position.x]
        
        # Check if there's already a seedling
        for asset in cell.assets:
            if asset.maturity_time is not None:
                self.log_event(f"Bot {bot.controller_id} failed to plant {asset_type.name} (seedling exists) at ({bot.position.x}, {bot.position.y})")
                return
        
        # Create corresponding seedling type
        seedling_map = {
            AssetType.ORE: AssetType.ORE_SEEDLING,
            AssetType.PLANT: AssetType.PLANT_SEEDLING,
            AssetType.COAL: AssetType.COAL_SEEDLING
        }
        
        # Plant new seedling
        seedling = Asset(
            type=seedling_map[asset_type],
            amount=1,  # Amount will be set when it matures
            maturity_time=self.seedling_maturity_time
        )
        cell.assets.append(seedling)
        self.log_event(f"Bot {bot.controller_id} planted {asset_type.name} seedling at ({bot.position.x}, {bot.position.y})")

    def mature_seedlings(self) -> None:
        """Process seedling maturation for all cells."""
        for row in self.map:
            for cell in row:
                # Track seedlings that need to be removed
                seedlings_to_remove = []
                mature_assets = {}  # Track mature assets by type
                
                # First pass: identify and process seedlings
                for asset in cell.assets[:]:  # Create a copy to safely iterate
                    if asset.maturity_time is not None:
                        asset.maturity_time -= 1
                        if asset.maturity_time <= 0:
                            seedlings_to_remove.append(asset)
                            mature_type = SEEDLING_TO_ASSET[asset.type]
                            mature_assets[mature_type] = mature_assets.get(mature_type, 0) + asset.amount
                
                # Second pass: remove matured seedlings
                for seedling in seedlings_to_remove:
                    if seedling in cell.assets:  # Check if still exists
                        cell.assets.remove(seedling)
                
                # Third pass: update or create mature assets
                for mature_type, total_amount in mature_assets.items():
                    # Find existing mature asset of this type
                    existing = None
                    for asset in cell.assets:
                        if asset.type == mature_type and asset.maturity_time is None:
                            existing = asset
                            break
                    
                    if existing:
                        # Update existing asset
                        existing.amount += total_amount
                    else:
                        # Create new mature asset
                        cell.assets.append(Asset(
                            type=mature_type,
                            amount=total_amount,
                            maturity_time=None
                        ))

    def create_bot(self, controller: Controller, position: Position, initial_deck: List[Card]) -> None:
        """Create a new bot for the given controller"""
        # Check if controller has enough minerals
        if controller.resources[ResourceType.MINERAL] < self.costs['new_bot']:
            raise ValueError("Not enough minerals to create bot")
        
        # Check if position is valid and empty
        if not (0 <= position.x < self.width and 0 <= position.y < self.height):
            raise ValueError("Invalid position")
        if self.map[position.y][position.x].bots:
            raise ValueError("Position already occupied")
        
        # Create and place bot
        controller.resources[ResourceType.MINERAL] -= self.costs['new_bot']
        bot = Bot(position, initial_deck, controller.id)
        controller.bots.append(bot)
        self.map[position.y][position.x].bots.add(bot)

    def modify_deck(self, bot: Bot, add_card: Optional[Card] = None, remove_index: Optional[int] = None) -> None:
        """Add or remove a card from a bot's deck"""
        print(f"MODIFYING DECK! {bot}")
        controller = self.controllers[bot.controller_id]
        
        # Check if controller has enough biomass
        if controller.resources[ResourceType.BIOMASS] < self.costs['modify_deck']:
            self.log_event("Not enough biomass to modify deck")
        
        # Deduct cost from controller's resources
        controller.resources[ResourceType.BIOMASS] -= self.costs['modify_deck']
        
        if add_card is not None:
            bot.deck.append(add_card)
        if remove_index is not None:
            print(f"removing: {remove_index}")
            if 0 <= remove_index < len(bot.deck):
                bot.deck.pop(remove_index)
            else:
                raise ValueError("Invalid deck index")

    def generate_uniform_assets(self, distribution: Dict[AssetType, int]) -> None:
        """Generate assets uniformly across the map"""
        available_cells = [(x, y) for x in range(self.width) 
                          for y in range(self.height)]
        
        for asset_type, count in distribution.items():
            # Ensure count doesn't exceed available cells
            count = min(count, len(available_cells))
            
            # Select random positions
            positions = random.sample(available_cells, count)
            
            # Place assets
            for x, y in positions:
                # Set maturity time for seedlings
                maturity_time = None
                if asset_type in [AssetType.ORE_SEEDLING, AssetType.PLANT_SEEDLING, AssetType.COAL_SEEDLING]:
                    maturity_time = self.seedling_maturity_time
                
                asset = Asset(
                    type=asset_type,
                    amount=random.randint(1, 5),
                    maturity_time=maturity_time
                )
                self.map[y][x].assets.append(asset)
                available_cells.remove((x, y))

    def check_victory(self) -> Optional[Controller]:
        """Check if any controller has met the victory conditions"""
        for controller in self.controllers:
            print(f"checking victory for Controller {controller.id}")
            victory = True
            for resource_type, amount in self.victory_conditions.items():
                if controller.resources[resource_type] < amount:
                    victory = False
                    print(f"...failed to meet victory condition for {resource_type.name}...")
                    break
            if victory:
                print(f"...victory condition met for {controller}...")
                self.state = 'victory'
                self.victors.append(controller)
                # return controller
        return None

    def process_controller_turn(self, controller: Controller, action: dict) -> None:
        """Process a single controller's turn based on their chosen action"""
        action_type = action['type']
        
        if action_type == 'create_bot':
            self.create_bot(
                controller,
                Position(action['x'], action['y']),
                action['deck']
            )
        elif action_type == 'modify_deck':
            self.modify_deck(
                action['bot'],
                action.get('add_card'),
                action.get('remove_index')
            )
        elif action_type == 'bot_actions':
            self.process_bot_actions(
                controller,
                action['energy_spent']
            )
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    def log_event(self, message: str) -> None:
        """Add an event to the log with current day and hour"""
        self.event_log.append({
            'day': self.day,
            'hour': self.hour,
            'message': message
        })

    def is_valid_position(self, position: Position) -> bool:
        """Check if a position is within the game map boundaries"""
        return (0 <= position.x < self.width and 
                0 <= position.y < self.height)

    def process_controller_action(self, controller: Controller, action_type: ControllerActionType, parameters: Dict) -> None:
        """Process a single controller action."""
        # Calculate hour cost
        hour_cost = 0
        if action_type == ControllerActionType.TAKE_BOT_ACTIONS:
            energy_points = parameters.get('energy_points')
            if energy_points is None:
                raise ValueError("energy_points parameter required for TAKE_BOT_ACTIONS")
            hour_cost = energy_points * self.hour_costs['bot_action']
        elif action_type == ControllerActionType.MODIFY_DECK:
            hour_cost = self.hour_costs['modify_deck']
        elif action_type == ControllerActionType.CREATE_BOT:
            hour_cost = self.hour_costs['new_bot']

        # Check if we have enough hours left in the day
        print(f"About to advance time, hour cost: {hour_cost}...")
        if not self.advance_time(hour_cost):
            raise ValueError(f"Not enough hours left in the day for {action_type.name}")
        print(f"...advanced time, hour cost: {self.hour}...")
        # Process the action
        if action_type == ControllerActionType.TAKE_BOT_ACTIONS:
            if energy_points > controller.get_total_resources():
                raise ValueError(f"Insufficient resources for {energy_points} energy points")
            self.process_bot_actions(controller, energy_points)


        elif action_type == ControllerActionType.MODIFY_DECK:
            bot_id = parameters.get('bot_id')
            cards = parameters.get('cards')
            removed_ids = parameters.get('removed_ids')
            
            if bot_id is None:
                raise ValueError("bot_id parameter required for MODIFY_DECK")
            if bot_id >= len(controller.bots):
                raise ValueError(f"Invalid bot_id: {bot_id}")
            if self.costs['modify_deck'] > controller.resources[ResourceType.BIOMASS]:
                raise ValueError("Insufficient biomass to modify deck")
            
            bot = controller.bots[bot_id]
            
            # Handle card removal
            if removed_ids is not None:
                # Sort indices in reverse order to avoid shifting issues
                for index in sorted(removed_ids, reverse=True):
                    if 0 <= index < len(bot.deck):
                        bot.deck.pop(index)
                    else:
                        raise ValueError(f"Invalid deck index: {index}")
            # Handle card addition
            elif cards is not None:
                for card_dict in cards:
                    try:
                        action_type = ActionType[card_dict['action_type']]
                        if action_type == ActionType.MOVE:
                            parameter = Direction[card_dict['parameter']]
                        else:  # HARVEST or PLANT
                            parameter = AssetType[card_dict['parameter']]
                        card = Card(action_type, parameter)
                        self.modify_deck(bot, add_card=card)
                    except (KeyError, ValueError) as e:
                        raise ValueError(f"Invalid card format: {e}")
            else:
                raise ValueError("Either cards or removed_ids parameter required for MODIFY_DECK")

        elif action_type == ControllerActionType.CREATE_BOT:
            if self.costs['new_bot'] > controller.get_total_resources():
                raise ValueError("Insufficient resources to create new bot")
            new_position = Position(controller.starting_position.x, controller.starting_position.y)
            new_bot = Bot(new_position, [], controller.id)
            controller.bots.append(new_bot)
            self.map[new_position.y][new_position.x].bots.add(new_bot)
            controller.deduct_resources(self.costs['new_bot'])

        print(f"PCA, hour now: {self.hour}")    
        self.log_event(f"Controller {controller.id} performed {action_type.name}")

    def advance_time(self, hours: int) -> bool:
        """Advance the game time by the specified number of hours.
        Returns False if advancing time would exceed the current day."""
        if self.hour + hours > self.hours_per_day:
            return False
        
        print(f"Advancing time {hours} hours. From {self.hour}.")
        self.hour += hours
        if self.hour >= self.hours_per_day:
            self.hour = 0
            self.day += 1
            # Process day-end events like seedling maturation
            self.mature_seedlings()
            
        return True 