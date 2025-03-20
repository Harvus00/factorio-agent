"""
Factorio Agent Main Module

This is the main entry point for the Factorio agent. It initializes the agent,
connects to the Factorio server via RCON, and runs the agent's main loop.
"""

import json
import os
import time
import logging
import toml
import asyncio
from openai import OpenAI
from agents import Agent, Runner, set_default_openai_key
from api.agent_tools import (
    get_available_prototypes,
    get_player_position,
    move_player,
    find_entities,
    place_entity,
    remove_entity,
    insert_item,
    remove_item,
    get_inventory
)

# Load configuration
config = toml.load("config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# Configure logging
logging.basicConfig(
    level=getattr(logging, config["logging"]["level"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=config["logging"]["file"]
)
logger = logging.getLogger('factorio_agent')

# Create an agent
factorio_agent = Agent(
    name="Factorio Agent",
    handoff_description="Specialist agent for playing Factorio.",
    instructions=config["agent"]["system_prompt"],
    tools=[
        get_available_prototypes,
        get_player_position,
        move_player,
        find_entities,
        place_entity,
        remove_entity,
        insert_item,
        remove_item,
        get_inventory,
    ],
)

async def read_game_state():
    """
    Read the current game state.
    
    Returns:
        Dict: The current game state
    """
    # Get player position
    position = get_player_position()
    
    # Get nearby entities
    entities = find_entities(
        radius=20,
        position_x=position.get('x', 0),
        position_y=position.get('y', 0)
    )
    
    # Get player inventory
    inventory = get_inventory()
    
    return {
        "player_position": position,
        "nearby_entities": entities,
        "inventory": inventory
    }

async def get_state_delta(current_state, last_state):
    """
    Calculate the difference between the current and last game state.
    
    Args:
        current_state: The current game state
        last_state: The previous game state
        
    Returns:
        Dict: The changes in game state
    """
    if not last_state:
        return current_state
        
    delta = {}
    
    # Check for position changes
    if current_state["player_position"] != last_state["player_position"]:
        delta["player_position"] = current_state["player_position"]
    
    # Check for entity changes
    current_entities = {(e["name"], e["position"]["x"], e["position"]["y"]): e 
                       for e in current_state["nearby_entities"]}
    last_entities = {(e["name"], e["position"]["x"], e["position"]["y"]): e 
                    for e in last_state["nearby_entities"]}
    
    new_entities = [e for k, e in current_entities.items() if k not in last_entities]
    removed_entities = [e for k, e in last_entities.items() if k not in current_entities]
    
    if new_entities or removed_entities:
        delta["entity_changes"] = {
            "new": new_entities,
            "removed": removed_entities
        }
    
    # Check for inventory changes
    inventory_delta = {}
    for item, count in current_state["inventory"].items():
        last_count = last_state["inventory"].get(item, 0)
        if count != last_count:
            inventory_delta[item] = count - last_count
    
    if inventory_delta:
        delta["inventory_changes"] = inventory_delta
    
    return delta if delta else None

async def main():
    """Main Loop"""
    logger.info("Starting Factorio Agent")
    try:
        # Get initial game state
        current_state = await read_game_state()
        state_json = json.dumps(current_state, indent=2)
        
        # Send initial message to agent
        initial_message = f"""
        The world is now loaded and ready to play. The current game state is as follows:
        {state_json}
        
        Please analyze the current state and provide an initial strategy.
        """
        result = await Runner.run(factorio_agent, initial_message)
        logger.info(f"Agent response: {result.final_output}")
        
        # Main loop
        last_state = current_state
        step_count = 0
        max_steps = config["agent"]["max_steps"]
        step_delay = config["agent"]["step_delay"]
        
        while step_count < max_steps:
            # Read current game state
            current_state = await read_game_state()
            
            # Calculate state changes
            delta = await get_state_delta(current_state, last_state)
            
            if delta:
                # If state changed, notify agent
                delta_json = json.dumps(delta, indent=2)
                update_message = f"""
                The world has changed. The changes are as follows:
                {delta_json}
                
                Please analyze the changes and provide your next actions.
                """
                result = await Runner.run(factorio_agent, update_message)
                logger.info(f"Agent response: {result.final_output}")
            else:
                # If no changes, ask agent to continue
                continue_message = f"""
                The world has not changed. Please continue with your strategy or take a different approach.
                """
                result = await Runner.run(factorio_agent, continue_message)
                logger.info(f"Agent response: {result.final_output}")
            
            # Update last state and increment step counter
            last_state = current_state
            step_count += 1
            
            # Wait before next iteration
            await asyncio.sleep(step_delay)
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())