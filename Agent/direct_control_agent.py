import json
import os
import time
import logging
from agents import Agent, Runner, ComputerTool, set_default_openai_key, AsyncComputer
import asyncio
import toml

config = toml.load("config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='direct_agent.log'
)
logger = logging.getLogger('DA')

# Create an agent
direct_factorio_agent = Agent(
    name="Factorio Player Agent",
    handoff_description="Specialist agent for playing Factorio.",
    instructions="""You are a professional Factorio game player and control keyboard and cursor to interact with game directly.
    You don't have spesisfic goal, but you can explore the game world and try to build automated factory as big as possible.
    """,
    tools= ComputerTool(AsyncComputer)
)

async def main():
    update_message = f"""
    The world is now loaded and ready to play. 
    """
    result = await Runner.run(direct_factorio_agent, update_message)
    print(result.final_output)
    logger.info(f"Agent: {result.final_output}")
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())