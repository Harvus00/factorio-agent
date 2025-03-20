"""
Agent Tools Module

This module provides tool functions that can be used by the agent to interact
with the Factorio game through the FactorioInterface.
"""

import json
from typing import List, Dict, Any, Optional, Union, Tuple
from agents import function_tool
from api.factorio_interface import FactorioInterface

# Create a global interface instance
factorio = FactorioInterface()

@function_tool
def get_available_prototypes() -> Dict[str, List[str]]:
    """
    Get lists of available prototype names in the game.
    
    Returns:
        Dict with keys 'entities' and 'items', each containing a list of valid names
    """
    return factorio.get_available_prototypes()

@function_tool
def get_player_position() -> Dict[str, float]:
    """
    Get the player's current position in the game.
    
    Returns:
        Dict with 'x' and 'y' coordinates
    """
    position = factorio.get_player_position()
    if position:
        return position
    return {"x": 0, "y": 0}  # Default if position cannot be determined

@function_tool
def move_player(x: float, y: float) -> str:
    """
    Move the player to a specific position.
    
    Args:
        x: The x coordinate to move to
        y: The y coordinate to move to
        
    Returns:
        Status message
    """
    success = factorio.move_player(x, y)
    return "Player moved successfully" if success else "Failed to move player"

@function_tool
def find_entities(name: Optional[str] = None, 
                 type: Optional[str] = None,
                 radius: Optional[float] = None,
                 position_x: Optional[float] = None,
                 position_y: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Find entities in the game based on specified filters.
    
    Args:
        name: Entity prototype name to filter by
        type: Entity type to filter by
        radius: Radius of the search circle
        position_x: X coordinate of the center of the search circle
        position_y: Y coordinate of the center of the search circle
        
    Returns:
        List of entity data dictionaries
    """
    # If position not specified, use player position
    if radius and (position_x is None or position_y is None):
        player_pos = factorio.get_player_position()
        if player_pos:
            position_x = position_x or player_pos.get('x', 0)
            position_y = position_y or player_pos.get('y', 0)
    
    return factorio.get_entities(
        name=name, 
        type=type,
        position_x=position_x,
        position_y=position_y,
        radius=radius
    )

@function_tool
def place_entity(name: str, x: float, y: float, direction: float = 0) -> str:
    """
    Place an entity in the game.
    
    Args:
        name: The entity prototype name to create
        x: The x coordinate
        y: The y coordinate
        direction: The direction (0, 2, 4, 6 for N, E, S, W)
        
    Returns:
        Status message
    """
    success, message = factorio.place_entity(name, x, y, direction)
    return message

@function_tool
def remove_entity(name: str, x: float, y: float) -> str:
    """
    Remove an entity from the game.
    
    Args:
        name: The entity prototype name to remove
        x: The x coordinate
        y: The y coordinate
        
    Returns:
        Status message
    """
    success, message = factorio.remove_entity(name, x, y)
    return message

@function_tool
def insert_item(item: str, count: int, 
               entity: str = "player",
               x: Optional[float] = None, 
               y: Optional[float] = None) -> str:
    """
    Insert items into an inventory.
    
    Args:
        item: The item name to insert
        count: The count of the item
        entity: The name of the entity to insert into (default: "player")
        x: The x coordinate of the entity (if not player)
        y: The y coordinate of the entity (if not player)
        
    Returns:
        Status message
    """
    success, message = factorio.insert_item(item, count, "character_main", entity, x, y)
    return message

@function_tool
def remove_item(item: str, count: int, 
               entity: str = "player",
               x: Optional[float] = None, 
               y: Optional[float] = None) -> str:
    """
    Remove items from an inventory.
    
    Args:
        item: The item name to remove
        count: The count of the item
        entity: The name of the entity to remove from (default: "player")
        x: The x coordinate of the entity (if not player)
        y: The y coordinate of the entity (if not player)
        
    Returns:
        Status message
    """
    success, message = factorio.remove_item(item, count, entity, x, y)
    return message

@function_tool
def get_inventory(entity: str = "player",
                 x: Optional[float] = None, 
                 y: Optional[float] = None) -> Dict[str, int]:
    """
    Get inventory contents.
    
    Args:
        entity: The name of the entity to get from (default: "player")
        x: The x coordinate of the entity (if not player)
        y: The y coordinate of the entity (if not player)
        
    Returns:
        Dictionary mapping item names to counts
    """
    return factorio.get_inventory("character_main", entity, x, y)