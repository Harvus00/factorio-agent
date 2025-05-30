import logging
import toml
import asyncio
from src.agent import Agent, Runner, set_default_openai_key
from src.api.agent_tools import (
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

config = toml.load("config/config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='factorio_agent.log'
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
        get_inventory
    ],
)
"""TODO:
Optimize the agent's planning ability: Ensure that the agent can effectively decompose tasks and develop reasonable execution plans.
Improve the design of function tools: Ensure that function tools can provide clear and concise information and reduce the number of interactions that agents need to make.
Add error handling mechanisms: When the agent encounters an error during execution, it can detect and take appropriate measures in time, rather than blindly continue to try.
**Reduce unnecessary environment queries:** Optimize the agent's logic and reduce the number of times it queries the environment.
"""

async def main():
    """Main Loop"""
    logger.info("Starting Factorio Agent")
    get_player_position #unlock the commands ability which is locked by achievements system
    try:
        initial_message = """
        The world is now loaded and ready to play. Pls first use the tool function to get the current game state (player position, nearby entities, and inventory),
        then analyze the current state and provide an initial strategy.
        Remember to add appropriate filtering parameters when using find_entities to avoid returning too much information.
        """
        result = await Runner.run(factorio_agent, initial_message, max_turns=20)
        logger.info(f"agent response: {result.final_output}")

        step_count = 0
        max_steps = config["agent"].get("max_steps", 100)
        step_delay = config["agent"].get("step_delay", 5)
        while step_count < max_steps:
            await asyncio.sleep(step_delay)

            message = """
            Please proceed with your plan. First, use the utility function to get the latest game state,
            and then decide and execute the next action based on the current state and the results of your previous actions.
            Remember to add appropriate filtering parameters when using find_entities to avoid returning too much information.
            """

            result = await Runner.run(factorio_agent, message,max_turns=40)
            logger.info(f"Step {step_count + 1} - Agent response: {result.final_output}")
            
            step_count += 1

    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}",exc_info=True)
    finally:
        logger.info("Agent stopped")

if __name__ == "__main__":
    asyncio.run(main())