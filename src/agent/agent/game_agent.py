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
from agent.tool.tool_manager import get_tool_manager

config = toml.load("config/config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='factorio_agent.log'
)
logger = logging.getLogger('factorio_agent')

os.environ["LANGSMITH_TRACING"] = str(config["langsmith"]["tracing"]).lower()
os.environ["LANGSMITH_ENDPOINT"] = config["langsmith"]["endpoint"]
os.environ["LANGSMITH_API_KEY"] = config["langsmith"]["api_key"]
os.environ["LANGSMITH_PROJECT"] = config["langsmith"]["project"]

class DynamicToolDispatcher:
    """
    Dynamic Tool Dispatcher - Avoid losing memory by re-creating the agent
    Use a unified interface to dispatch dynamic generated tools
    """
    
    def __init__(self):
        self.logger = logging.getLogger('dynamic_tool_dispatcher')
        self.coding_agent = CodingAgent()
        self.tool_manager = get_tool_manager()
        self.dynamic_tools: Dict[str, Callable] = {}
        
        # Load existing dynamic tools
        self._load_existing_tools()
    
    def _load_existing_tools(self):
        try:
            all_tools = self.tool_manager.load_all_tools()
            self.dynamic_tools.update(all_tools)
            self.logger.info(f"Loaded {len(all_tools)} existing dynamic tools")
        except Exception as e:
            self.logger.error(f"Failed to load existing tools: {e}")
    
    async def request_new_tool(self, requirement: str, 
                              functionality_details: str = "",
                              suggested_name: str = "") -> Dict[str, Any]:
        """Request to generate a new tool"""
        try:
            self.logger.info(f"Request to generate a new tool: {requirement}")
            
            request_message = f"""
Generate a new Factorio Lua script tool based on:
requirement: {requirement}
functionality_details: {functionality_details}
suggested_name: {suggested_name if suggested_name else "auto_generated"}
"""
            result = await Runner.run(
                self.coding_agent.agent,
                input=request_message,
                max_turns=5
            )
            
            new_scripts = self.coding_agent.get_available_scripts_list()
            
            if not new_scripts:
                return {
                    "success": False,
                    "message": "No new tool generated",
                    "details": str(result.final_output)
                }
            
            latest_script = max(new_scripts, key=lambda x: x.get('created_at', ''))
            script_name = latest_script['name']
            
            # Hot load new tool
            loaded_tool = self._hot_load_tool(script_name)
            
            if loaded_tool:
                return {
                    "success": True,
                    "message": f"Successfully generated and loaded tool: {script_name}",
                    "tool_name": script_name,
                    "script_info": latest_script,
                    "agent_output": str(result.final_output)
                }
            else:
                return {
                    "success": False,
                    "message": f"Tool {script_name} generated successfully but failed to load",
                    "script_info": latest_script
                }
                
        except Exception as e:
            self.logger.error(f"Failed to request new tool: {e}")
            return {
                "success": False,
                "message": f"Error generating new tool: {str(e)}",
                "error": str(e)
            }
    
    def _hot_load_tool(self, tool_name: str) -> Optional[Callable]:
        """Hot load tool"""
        try:
            tool_func = self.tool_manager.load_tool(tool_name)
            if tool_func:
                self.dynamic_tools[tool_name] = tool_func
                self.logger.info(f"Successfully hot loaded tool: {tool_name}")
                return tool_func
            return None
        except Exception as e:
            self.logger.error(f"Failed to hot load tool {tool_name}: {e}")
            return None
            
    def refresh_tools(self) -> Dict[str, Any]:
        """Refresh dynamic tools (without re-creating the agent)"""
        try:
            all_tools = self.tool_manager.load_all_tools()
            old_count = len(self.dynamic_tools)
            self.dynamic_tools.update(all_tools)
            new_count = len(self.dynamic_tools)
            
            return {
                "success": True,
                "message": f"Refresh completed, tools increased from {old_count} to {new_count}",
                "loaded_tools": list(all_tools.keys()),
                "total_tools": new_count
            }
        except Exception as e:
            self.logger.error(f"Failed to refresh tools: {e}")
            return {
                "success": False,
                "message": f"Error refreshing tools: {str(e)}",
                "error": str(e)
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """List all available tools"""
        return {
            "dynamic_tools_count": len(self.dynamic_tools),
            "available_scripts_count": len(self.coding_agent.get_available_scripts_list()),
            "tool_manager_stats": self.tool_manager.get_usage_statistics(),
            "dynamic_tools": list(self.dynamic_tools.keys()),
            "available_scripts": [script['name'] for script in self.coding_agent.get_available_scripts_list()]
        }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute dynamic tool"""
        try:
            if tool_name not in self.dynamic_tools:
                return {
                    "success": False,
                    "message": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.dynamic_tools.keys())
                }
            
            tool_func = self.dynamic_tools[tool_name]
            parameters = parameters or {}
            
            result = tool_func(**parameters)
            
            return {
                "success": True,
                "message": f"Successfully executed tool: {tool_name}",
                "tool_result": result,
                "parameters_used": parameters
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing tool {tool_name}: {str(e)}",
                "error": str(e)
            }


class MainGameAgent:
    """
    Main game agent - designed to maintain memory and task continuity
    """
    
    def __init__(self):
        self.logger = logging.getLogger('main_game_agent')
        self.tool_dispatcher = DynamicToolDispatcher()
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
        
        dynamic_management_tools = [
            self._create_dynamic_tool_interface()
        ]
        
        all_tools = base_tools + dynamic_management_tools
        
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
- Use unified interface to manage and use dynamically generated action tools

Dynamic tool system:
Use manage_dynamic_tools interface to perform all dynamic tool operations:
- action="request": Request to generate a new action tool
- action="refresh": Refresh tool list
- action="list": List all available tools  
- action="execute": Execute specified tool
Current available dynamic tools: {list(self.tool_dispatcher.dynamic_tools.keys())}

Pls maintain autonomy and manage your own status and decision-making process step by step without waiting for additional instructions.
"""
        
        return Agent(
            name="Factorio Master Agent",
            handoff_description="Factorio master agent with dynamic tool generation and calling capabilities",
            instructions=instructions,
            tools=all_tools,
            model=config["openai"]["MODEL"],
            model_settings=ModelSettings(parallel_tool_calls=True)
        )
    
    def _create_dynamic_tool_interface(self):
        """Create unified dynamic tool management interface"""
        @function_tool
        async def manage_dynamic_tools(action: str, 
                                     tool_name: str = "",
                                     requirement: str = "",
                                     functionality_details: str = "",
                                     suggested_name: str = "",
                                     parameters_json: str = "{}") -> str:
            """
            Unified dynamic tool management interface
            
            Args:
                action: Action type ("request", "refresh", "list", "execute")
                tool_name: Tool name (used when action="execute")
                requirement: Tool requirement description (used when action="request")
                functionality_details: Functionality details (used when action="request")
                suggested_name: Suggested tool name (used when action="request")
                parameters_json: Tool parameters JSON string (used when action="execute")
                
            Returns:
                JSON string of operation result
            """
            try:
                if action == "request":
                    if not requirement:
                        return json.dumps({"success": False, "message": "Please provide tool requirement description"})
                    
                    result = await self.tool_dispatcher.request_new_tool(
                        requirement, functionality_details, suggested_name
                    )
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "refresh":
                    result = self.tool_dispatcher.refresh_tools()
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "list":
                    result = self.tool_dispatcher.list_tools()
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                elif action == "execute":
                    if not tool_name:
                        return json.dumps({"success": False, "message": "Please provide the tool name to execute"})
                    
                    try:
                        parameters = json.loads(parameters_json) if parameters_json else {}
                    except json.JSONDecodeError:
                        return json.dumps({"success": False, "message": f"Parameter JSON format error: {parameters_json}"})
                    
                    result = self.tool_dispatcher.execute_tool(tool_name, parameters)
                    return json.dumps(result, indent=2, ensure_ascii=False)
                
                else:
                    return json.dumps({
                        "success": False, 
                        "message": f"Unsupported action: {action}",
                        "supported_actions": ["request", "refresh", "list", "execute"]
                    })
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Dynamic tool management error: {str(e)}",
                    "error": str(e)
                }, ensure_ascii=False)
        
        return manage_dynamic_tools


async def main():
    """Main loop - maintain agent memory and task continuity"""
    logger.info("Starting Factorio master agent")
    
    master_agent = MainGameAgent()
    
    try:
        initial_message = """
        The world is now loaded and ready to play. 
        Please start:
        1. Request some new action tool if needed
        2. Execute the new tool to test if it works
        3. Get current game state
        4. Develop long-term strategy and goals
        """
        
        result = await Runner.run(master_agent.agent, initial_message, max_turns=20)
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
            3. If you need new features, continue using the dynamic tool management interface
        """

            result = await Runner.run(master_agent.agent, message, max_turns=40)
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