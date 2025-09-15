import logging
import os
import toml
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

from agents import Agent, Runner, set_default_openai_key, function_tool, set_trace_processors, ModelSettings
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from agent.tool.agent_tools import (
    get_player_position,
    move_player,
    search_entities,
    place_entity,
    remove_entity,
    insert_item,
    remove_item,
    get_inventory,
    query_wiki_knowledge_base
)
from agent.agent.coding_agent import CodingAgent
from agent.tool.unified_tool_manager import get_unified_tool_manager, LuaScriptProvider

config = toml.load("config/config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='factorio_agent.log'
)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

os.environ["LANGSMITH_TRACING"] = str(config["langsmith"]["tracing"]).lower()
os.environ["LANGSMITH_ENDPOINT"] = config["langsmith"]["endpoint"]
os.environ["LANGSMITH_API_KEY"] = config["langsmith"]["api_key"]
os.environ["LANGSMITH_PROJECT"] = config["langsmith"]["project"]


class MainGameAgent:
    """
    Main game agent - use unified tool manager to manage dynamic tools
    """
    
    def __init__(self):
        self.logger = logging.getLogger('main_game_agent')
        
        self.tool_manager = get_unified_tool_manager()
        
        # Initialize CodingAgent and register as tool provider
        self.coding_agent = CodingAgent()
        lua_provider = LuaScriptProvider(self.coding_agent)
        self.tool_manager.register_provider(lua_provider)
        self.tool_manager.load_all_tools()

        # Spawn master agent for game play
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        # Base tools
        base_tools = [
            get_player_position,
            move_player,
            search_entities,
            place_entity,
            remove_entity,
            insert_item,
            remove_item,
            get_inventory,
            query_wiki_knowledge_base
        ]
        
        tool_management_tools = [
            self._create_unified_tool_interface()
        ]
        
        all_tools = base_tools + tool_management_tools

        # Get current available dynamic tools list
        current_tools = self.tool_manager.list_tools()
        available_tools_list = list(current_tools.get("tools", {}).keys())
        
        instructions = f"""
You are a professional Factorio game player and interact with the game using API tools, with dynamic action tool generation.

Workflow:
1. Use tools to get the current game state and analyze the state
2. Make a short-term plan based on the state
3. Execute the plan and record the results
4. Adjust the subsequent plan based on the results
5. Repeat the above steps until the game is over

Basic capabilities:
- Use base tools to interact with Factorio game
- Query knowledge base to get entity Wiki information(when you are not sure about the valid game parameters or features)
- Use unified tool management interface to create, manage and execute dynamic tools

Dynamic tool system:
Use manage_tools interface for all tool operations:
- action="create": Create a new tool (specify requirement)
- action="list": List all available tools
- action="execute": Execute a specific tool
- action="remove": Remove a tool

Currently available dynamic tools: {available_tools_list}

Maintain autonomy and manage your own status and decision-making process step by step without waiting for additional instructions.
"""
        
        return Agent(
            name="Factorio Master Agent",
            handoff_description="Factorio master agent with unified dynamic tool management",
            instructions=instructions,
            tools=all_tools,
            model=config["openai"]["MODEL"],
            model_settings=ModelSettings(parallel_tool_calls=True)
        )
    
    def _create_unified_tool_interface(self):

        @function_tool
        async def manage_tools(action: str, 
                             tool_name: str = "",
                             requirement: str = "",
                             functionality_details: str = "",
                             suggested_name: str = "",
                             parameters_json: str = "") -> str:
            """
            Unified dynamic tool management interface
            
            Args:
                action: operation type ("create", "list", "execute", "remove")
                tool_name: tool name (use when execute/remove)
                requirement: tool requirement description (use when create)
                functionality_details: functionality details (use when create)
                suggested_name: suggested tool name (use when create)
                parameters_json: tool execution parameters (use when execute)
                
            Returns:
                JSON string of operation result
            """
            try:
                if action == "create":
                    if not requirement:
                        return json.dumps({"success": False, "message": "Please provide tool requirement description"})
                    
                    result = await self.tool_manager.create_tool(
                        requirement=requirement,
                        functionality_details=functionality_details,
                        suggested_name=suggested_name
                    )
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "list":
                    result = self.tool_manager.list_tools()
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "execute":
                    if not tool_name:
                        return json.dumps({"success": False, "message": "Please provide the tool name to execute"})
                    
                    try:
                        parameters = json.loads(parameters_json) if parameters_json else {}
                    except json.JSONDecodeError:
                        return json.dumps({"success": False, "message": f"Parameter JSON format error: {parameters_json}"})
                    
                    result = self.tool_manager.execute_tool(tool_name, parameters)
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "remove":
                    if not tool_name:
                        return json.dumps({"success": False, "message": "Please provide the tool name to remove"})
                    
                    result = self.tool_manager.remove_tool(tool_name)
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                else:
                    return json.dumps({
                        "success": False, 
                        "message": f"Unsupported action: {action}",
                        "supported_actions": ["create", "list", "execute", "remove"]
                    })
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Tool management error: {str(e)}",
                    "error": str(e)
                }, ensure_ascii=False)
        
        return manage_tools


async def main():
    """Main loop - maintain agent memory and task continuity"""
    logger.info("Starting Factorio master agent")
    
    master_agent = MainGameAgent()
    
    try:
        initial_message = """
        The world is now loaded and ready to play. 
        Please start:
        1. Check current available tools with action="list" 
        2. Create some new action tools if needed with action="create"
        3. Test the new tools with action="execute"
        4. Get current game state
        5. Develop long-term strategy and goals
        """
        
        result = await Runner.run(master_agent.agent, initial_message, max_turns=100)
        logger.info(f"Agent response: {result.final_output}")

        step_count = 0
        max_steps = config["agent"].get("max_steps", 100)
        step_delay = config["agent"].get("step_delay", 5)
        
        while step_count < max_steps:
            await asyncio.sleep(step_delay)

            message = """
            Please continue executing your plan.
            1. Get the latest game state
            2. Decide the next step based on your long-term goals and previous action results
            3. If you need new features, use manage_tools interface to create them
        """

            result = await Runner.run(master_agent.agent, message, max_turns=100)
            logger.info(f"Step {step_count + 1} - Agent response: {result.final_output}")
            
            step_count += 1

    except KeyboardInterrupt:
        logger.info("User stopped the agent")
    except Exception as e:
        logger.error(f"Main loop error: {e}", exc_info=True)
    finally:
        logger.info("Master agent stopped")


if __name__ == "__main__":
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    asyncio.run(main())