from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from game import Game
from game_interface import GameInterface
from game_enums import ControllerActionType

# Load initial game configuration
import json
with open('game_config_dev.json', 'r') as f:
    config = json.load(f)

# Create global game instance
game = Game(config)

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

class TurnOrder(BaseModel):
    controller_id: int
    action_type: str  # Will be converted to ControllerActionType
    parameters: Dict[str, Union[int, str, List, Dict]]

class TurnOrders(BaseModel):
    orders: List[TurnOrder]

@app.get("/game/state")
async def get_game_state():
    """Get the current game state"""
    try:
        # Create interface instance to get state
        interface = GameInterface()
        interface.game = game  # Attach our game instance
        return interface.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 