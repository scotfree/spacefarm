from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from game import Game
from game_interface import GameInterface
from game_enums import ControllerActionType

# Load level configurations
import json
LEVEL_CONFIGS = {}

def load_level_configs():
    global LEVEL_CONFIGS
    level_files = {
        'rare': 'rare_config.json',
        'medium_rare': 'medium_rare_config.json'
    }
    for level_name, filename in level_files.items():
        with open(filename, 'r') as f:
            LEVEL_CONFIGS[level_name] = json.load(f)

# Load initial configurations
load_level_configs()

# Create global game instance with default level
game = Game(LEVEL_CONFIGS['rare'])
current_level = 'rare'

# Create FastAPI app
app = FastAPI(title="SpaceDew Game API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

class TurnOrder(BaseModel):
    controller_id: int
    action_type: str  # Will be converted to ControllerActionType
    parameters: Dict[str, Union[int, str, List, Dict]]

class TurnOrders(BaseModel):
    orders: List[TurnOrder]

@app.get("/game/levels")
async def get_levels():
    """Get list of available levels"""
    return {
        "levels": list(LEVEL_CONFIGS.keys()),
        "current_level": current_level
    }

@app.post("/game/restart")
async def restart_game(level: Optional[str] = None):
    """Restart the game with optionally specified level"""
    global game, current_level
    
    # If no level specified, use current level
    if level is None:
        level = current_level
    
    # Validate level exists
    if level not in LEVEL_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
    
    # Create new game instance with specified level config
    try:
        game = Game(LEVEL_CONFIGS[level])
        current_level = level
        
        # Return initial game state
        interface = GameInterface()
        interface.game = game
        return interface.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/game/state")
async def get_game_state():
    """Get current game state"""
    interface = GameInterface()
    interface.game = game
    return interface.get_game_state()

@app.get("/game/grid", response_class=HTMLResponse)
async def get_game_grid():
    """Get the HTML representation of the game grid"""
    try:
        grid_html = GameInterface.generate_html_grid(game)
        return grid_html
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/turn")
async def process_turn(turn_orders: TurnOrders):
    """Process a game turn with the provided orders"""
    try:
        # Convert string action_types to ControllerActionType enum
        orders = []
        for order in turn_orders.orders:
            # Convert action_type string to enum
            try:
                action_type = ControllerActionType[order.action_type]
            except KeyError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid action_type: {order.action_type}"
                )
            
            # Create order dict with enum
            orders.append({
                'controller_id': order.controller_id,
                'action_type': action_type,
                'parameters': order.parameters
            })
        
        # Process the turn
        game.process_turn(orders)
        
        # Return updated game state
        interface = GameInterface()
        interface.game = game
        return interface.get_game_state()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def get_game_client():
    """Serve the game client HTML file"""
    return FileResponse("game_client.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 