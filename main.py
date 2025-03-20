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

config = toml.load("config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='factorio_agent.log'
)
logger = logging.getLogger('factorio_agent')

# Create an agent
factorio_strategy_agent = Agent(
    name="Factorio Agent",
    handoff_description="Specialist agent for playing Factorio.",
    instructions=config["agents"]["system_prompt"],
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
async def read_game_state():
    """
    读取当前游戏状态
    Returns:
        Dict: 当前游戏状态
    """
    position = get_player_position()
    entities = find_entities(
        radius=20,
        position_x=position.get('x', 0),
        position_y=position.get('y', 0)
    )
    inventory = get_inventory()
    return {
        "player_position": position,
        "nearby_entities": entities,
        "inventory": inventory
    }

async def main():
    """Main Loop"""
    logger.info("Starting Factorio Agent")
    try:
        current_state = await read_game_state()
        initial_message = """
        The world is now loaded and ready to play. Pls first use the tool function to get the current game state (player position, nearby entities, and inventory),
        then analyze the current state and provide an initial strategy.
        Remember to add appropriate filtering parameters when using find_entities to avoid returning too much information.
        """
        result = await Runner.run(factorio_strategy_agent, initial_message)
        logger.info(f"agent response: {result.final_output}")

        step_count = 0
        max_steps = config["agent"].get("max_steps", 100)
        step_delay = config["agent"].get("step_delay", 5)
        while step_count < max_steps:
            await asyncio.sleep(step_delay)
            # 构建消息，让代理继续执行下一步
            message = """
            Please proceed with your plan. First, use the utility function to get the latest game state,
            and then decide and execute the next action based on the current state and the results of your previous actions.
            Remember to add appropriate filtering parameters when using find_entities to avoid returning too much information.
            """
            # 运行代理
            result = await Runner.run(factorio_agent, message)
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