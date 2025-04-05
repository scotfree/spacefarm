from typing import Dict
from game_enums import AssetType, ResourceType, ActionType, Direction
from game import Game
from game_objects import Cell, Position, Bot, Asset

class GameInterface:
    # Color scheme for different asset types
    ASSET_COLORS = {
        AssetType.ORE: "#D4A76A",  # Orange-tinted gray
        AssetType.PLANT: "#228B22",  # Forest green
        AssetType.COAL: "#463E3F",  # Dark gray
        AssetType.ORE_SEEDLING: "#F0D5A9",  # Lighter orange-gray
        AssetType.PLANT_SEEDLING: "#98FB98",  # Lighter green
        AssetType.COAL_SEEDLING: "#8C8687",  # Lighter gray
    }
    
    @staticmethod
    def generate_html_grid(game: Game) -> str:
        """Generate an HTML representation of the game map"""
        
        # Generate CSS styles
        styles = """
            <style>
                .game-grid {
                    display: grid;
                    grid-template-columns: repeat(%d, 60px);
                    gap: 2px;
                    background-color: #333;
                    padding: 2px;
                    font-family: monospace;
                }
                .cell {
                    width: 60px;
                    height: 60px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    font-size: 12px;
                    position: relative;
                    background-color: #9BA2A7;
                    overflow: hidden;
                }
                .coordinates {
                    position: absolute;
                    top: 2px;
                    left: 2px;
                    color: #999;
                    font-size: 10px;
                }
                .bot-label {
                    position: absolute;
                    top: 2px;
                    right: 2px;
                    background-color: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 1px 3px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                .asset-label {
                    color: white;
                    text-align: center;
                    margin: 2px 0;
                    font-weight: bold;
                }
            </style>
            """ % game.width
        
        # Generate grid HTML
        grid_html = '<div class="game-grid">'
        for y in range(game.height):
            for x in range(game.width):
                cell = game.map[y][x]
                
                # Determine cell background color based on assets
                bg_color = "#9BA2A7"  # Default gray
                if cell.assets:
                    bg_color = GameInterface.ASSET_COLORS[cell.assets[0].type]
                
                cell_html = f'<div class="cell" style="background-color: {bg_color}">'
                
                # Add coordinates
                cell_html += f'<div class="coordinates">({x},{y})</div>'
                
                # Add bot label if there are bots
                if cell.bots:
                    # Count bots per controller
                    bot_counts = {}
                    for bot in cell.bots:
                        bot_counts[bot.controller_id] = bot_counts.get(bot.controller_id, 0) + 1
                    
                    # Create bot labels
                    bot_labels = []
                    for controller_id, count in bot_counts.items():
                        label = f'C{controller_id}'
                        if count > 1:
                            label += f'×{count}'
                        bot_labels.append(label)
                    
                    cell_html += f'<div class="bot-label">{" ".join(bot_labels)}</div>'
                
                # Add asset labels
                if cell.assets:
                    for asset in cell.assets:
                        label = GameInterface.get_asset_label(asset)
                        cell_html += f'<div class="asset-label">{label}</div>'
                
                cell_html += '</div>'
                grid_html += cell_html
        
        grid_html += '</div>'
        return styles + '\n' + grid_html
    
    @staticmethod
    def get_game_state_summary(game: Game) -> str:
        """Generate a summary of game state including resources and victory conditions"""
        summary = ["<div style='font-family: monospace; margin: 10px 0;'>"]
        
        # Add day and hour counter
        summary.append(f"Day {game.day}, Hour {game.hour}<br>")
        
        # Add event log
        if game.event_log:
            summary.append("<br>Event Log:")
            # Show last 5 events in reverse chronological order
            for event in reversed(game.event_log[-5:]):
                summary.append(f"<br>Day {event['day']}, Hour {event['hour']}: {event['message']}")
            summary.append("<br>")
        
        # Add controller information
        for controller in game.controllers:
            #summary.append(f"<br>Controller {controller.id}:")
            #summary.append(f"<br>Bots: {len(controller.bots)}")
            
            summary.append(f"<br>Controller {controller.id}:")
            summary.append(f"<br>Bots: {len(controller.bots)}")


            # Add deck information for each bot
            for i, bot in enumerate(controller.bots):
                summary.append(f"<br>Bot {i} deck: [")
                card_labels = []
                for card in bot.deck:
                    if card.action_type == ActionType.MOVE:
                        if card.parameter == Direction.RANDOM:
                            label = "M?"  # Random move shown as M?
                        else:
                            label = f"M{card.parameter.name[0]}"  # M[N/S/E/W]
                    elif card.action_type == ActionType.HARVEST:
                        label = f"H{card.parameter.name[0]}"  # H[O/P/C]
                    elif card.action_type == ActionType.PLANT:
                        label = f"P{card.parameter.name[0]}"  # P[O/P/C]
                    card_labels.append(label)
                summary.append(" ".join(card_labels) + "]")
            
           
        # Add victory conditions
        # summary.append("<br><br>Victory Conditions:")
        # for resource_type, amount in game.victory_conditions.items():
        #     summary.append(f"<br> - {resource_type.name}: {amount}")
        
        summary.append("</div>")
        return '\n'.join(summary)

    @staticmethod
    def _generate_bot_label(bots):
        if not bots:
            return ""
        # Group bots by controller
        controller_counts = {}
        for bot in bots:
            controller_counts[bot.controller_id] = controller_counts.get(bot.controller_id, 0) + 1
        
        # Generate labels
        labels = []
        for controller_id, count in controller_counts.items():
            if count > 1:
                labels.append(f'C{controller_id}×{count}')
            else:
                labels.append(f'C{controller_id}')
        return ', '.join(labels)

    def _generate_cell_html(self, cell: Cell, x: int, y: int) -> str:
        # Get background color based on cell contents
        bg_color = self._get_cell_background_color(cell)
        
        html = f'<div class="cell" style="background-color: {bg_color}">'
        html += f'<div class="coordinates">({x},{y})</div>'
        
        # Display assets
        for asset_type, count, maturity in self._get_asset_summary(cell):
            label = f"{asset_type.name}"
            if maturity is not None:
                label += f"({maturity})"
            label += f"×{count}"
            html += f'<div class="asset-label">{label}</div>'
        
        # Display bots grouped by controller
        bot_counts = {}
        for bot in cell.bots:
            bot_counts[bot.controller_id] = bot_counts.get(bot.controller_id, 0) + 1
        
        for controller_id, count in bot_counts.items():
            label = f"C{controller_id}"
            if count > 1:
                label += f"×{count}"
            html += f'<div class="bot-label">{label}</div>'
        
        html += '</div>'
        return html 

    @staticmethod
    def get_asset_label(asset: Asset) -> str:
        """Generate a display label for an asset."""
        # Get short name for asset type
        type_map = {
            AssetType.ORE: "ORE",
            AssetType.PLANT: "PLT",
            AssetType.COAL: "COL",
            AssetType.ORE_SEEDLING: "ORS",
            AssetType.PLANT_SEEDLING: "PLS",
            AssetType.COAL_SEEDLING: "CLS"
        }
        
        label = type_map[asset.type]
        
        # Add maturity time for seedlings
        if asset.maturity_time is not None:
            label += f"({asset.maturity_time})"
        
        # Add amount if more than 1
        if asset.amount > 1:
            label += f"×{asset.amount}"
        
        return label 

    def get_game_state(self) -> dict:
        """Returns a complete representation of the game state in JSON format."""
        state = {
            'day': self.game.day,
            'hour': self.game.hour,
            'hours_per_day': self.game.hours_per_day,
            'map_size': {
                'width': self.game.width,
                'height': self.game.height
            },
            'costs': self.game.costs,
            'hour_costs': self.game.hour_costs,
            'victory_conditions': {
                resource_type.name: amount 
                for resource_type, amount in self.game.victory_conditions.items()
            },
            'controllers': [],
            'state': self.game.state,
            'victors': self.game.victors,
            'map': []
        }
        
        # Add controllers state
        for controller in self.game.controllers:
            controller_state = {
                'id': controller.id,
                'resources': {
                    resource_type.name: amount 
                    for resource_type, amount in controller.resources.items()
                },
                'bots': []
            }
            
            # Add bots for this controller
            for bot in controller.bots:
                bot_state = {
                    'position': {
                        'x': bot.position.x,
                        'y': bot.position.y
                    },
                    'deck': [
                        {
                            'action_type': card.action_type.name,
                            'parameter': card.parameter.name
                        }
                        for card in bot.deck
                    ]
                }
                controller_state['bots'].append(bot_state)
            
            state['controllers'].append(controller_state)
        
        # Add map state
        for y in range(self.game.height):
            row = []
            for x in range(self.game.width):
                cell = self.game.map[y][x]
                cell_state = {
                    'position': {'x': x, 'y': y},
                    'assets': [
                        {
                            'type': asset.type.name,
                            'amount': asset.amount,
                            'maturity_time': asset.maturity_time
                        }
                        for asset in cell.assets
                    ],
                    'bots': [
                        {
                            'controller_id': bot.controller_id,
                            'position': {
                                'x': bot.position.x,
                                'y': bot.position.y
                            }
                        }
                        for bot in cell.bots
                    ]
                }
                row.append(cell_state)
            state['map'].append(row)
        
        # Add event log
        state['event_log'] = self.game.event_log
        
        return state 