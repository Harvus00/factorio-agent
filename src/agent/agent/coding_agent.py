"""
Coding Agent Module

This module implements a coding agent capable of dynamically generating
Factorio Lua scripts and wrapping them into reusable function tools.
"""
import logging
import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from agents import Agent, Runner, function_tool, set_default_openai_key, set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from agents.extensions.models.litellm_model import LitellmModel
import toml
import json

from agent.tool.agent_tools import (
    query_wiki_knowledge_base,
    query_api_knowledge_base
)
import lupa.lua52 as lupa

config = toml.load("config/config.toml")
set_default_openai_key(config["openai"]["OPENAI_API_KEY"])

os.environ["LANGSMITH_TRACING"] = str(config["langsmith"]["tracing"]).lower()
os.environ["LANGSMITH_ENDPOINT"] = config["langsmith"]["endpoint"]
os.environ["LANGSMITH_API_KEY"] = config["langsmith"]["api_key"]
os.environ["LANGSMITH_PROJECT"] = config["langsmith"]["project"]

class CodingAgent:
    """
    Advanced coding agent for dynamic Factorio Lua script generation
    """
    
    def __init__(self, config_path: str = "config/config.toml"):
        """
        Initialize the coding agent
        
        Args:
            config_path: Path to configuration file
        """
        self.config = toml.load(config_path)
        self.logger = self._setup_logging()
        
        # Storage paths - only for temporary generation, actual storage managed by UnifiedToolManager
        self.tools_dir = Path("src/agent/tool/generated")
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Lua runtime for validation if available
        self.lua_runtime = self._init_lua_runtime()
        
        # Tool manager reference - will be set by UnifiedToolManager
        self.tool_manager = None
        
        # Create the agent
        self.agent = self._create_agent()
        
    def set_tool_manager(self, tool_manager):
        """
        Set the tool manager reference (called by UnifiedToolManager)
        
        Args:
            tool_manager: Reference to the UnifiedToolManager instance
        """
        self.tool_manager = tool_manager
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='coding_agent.log'
        )
        return logging.getLogger('coding_agent')
    
    def _init_lua_runtime(self) -> Optional[Any]:
        """Initialize Lua runtime for validation"""
        try:
            return lupa.LuaRuntime(unpack_returned_tuples=True)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Lua runtime: {e}")
            return None
    
    def _create_agent(self) -> Agent:
        """Create the coding agent with appropriate tools and instructions"""
        
        system_prompt = """You are a Factorio Lua scripting specialist. Your role is to generate reusable, parameterized Lua scripts for automating Factorio gameplay.

CRITICAL: Generate PARAMETERIZED scripts using placeholders that can be dynamically replaced by the Python wrapper.

Key Guidelines for Lua Script Generation:
- Always start scripts with "/sc " prefix for Factorio console commands
- Always query api docs through query_api_knowledge_base tool to use proper Factorio Runtime API (game.*, player.*, surface.*, etc.)
- Include proper error handling and user feedback via rcon.print()
- Follow Lua syntax and conventions
- Test edge cases (no player, invalid parameters, etc.)

PARAMETERIZATION RULES:
- Use {parameter_name} placeholders for dynamic values
- Examples: {entity_name}, {radius}, {item_name}, {quantity}, {x_position}, {y_position}
- Always provide default values in comments when possible
- Make scripts as reusable as possible by parameterizing appropriate values

Common Factorio API Patterns:
- game.players[1] or game.get_player(1) for player access
- game.surfaces[1] for surface operations  
- surface.find_entities_filtered() for finding entities
- player.teleport() for movement

Example Parameterized Script for Entity Teleportation:
```
/sc 
-- Teleport player to nearest {entity_name} within {radius} tiles
-- Default: entity_name="iron-ore", radius=50
local player = game.players[1]

if not player then
    rcon.print("Error: No player found")
    return
end

local entity_name = "{entity_name}" -- e.g., "iron-ore", "copper-ore", "coal"
local search_radius = {radius} -- e.g., 50, 100, 200

local entities = game.surfaces[1].find_entities_filtered{
    position=player.position, 
    name=entity_name, 
    radius=search_radius
}

if entities and #entities > 0 then
    player.teleport(entities[1].position)
    rcon.print("Teleported to " .. entity_name .. " at position " .. entities[1].position.x .. ", " .. entities[1].position.y)
else
    rcon.print("No " .. entity_name .. " found within " .. search_radius .. " tiles")
end
```

Always generate COMPLETE, WORKING, PARAMETERIZED Lua scripts that use placeholders for dynamic values. Focus on creating reusable templates that can handle multiple scenarios through parameter substitution.

After generating the parameterized Lua code, use save_generated_lua_script to save it with an appropriate name, description, and parameter definitions.
"""

        # Create tool functions that reference this instance
        def save_generated_lua_script(script_name: str, lua_code: str, description: str, parameters_json: str = "{}") -> str:
            """
            Save a generated Lua script to the registry and filesystem.
            This tool should be used by the AI after generating the actual Lua code.
            
            Args:
                script_name: Name for the script
                lua_code: The complete Lua script code (including /sc prefix)
                description: Description of what the script does  
                parameters_json: JSON string of parameters (optional)
            
            Returns:
                Status message
            """
            return self.save_lua_script(script_name, lua_code, description, parameters_json)
        
        def list_available_scripts_tool() -> str:
            """
            List all available scripts
            
            Returns:
                JSON string of scripts list
            """
            scripts_list = self.get_available_scripts_list()
            return json.dumps(scripts_list, indent=2)
        
        def get_script_info_tool(script_name: str) -> str:
            """
            Get information about a specific script
            
            Args:
                script_name: Name of the script
                
            Returns:
                JSON string with script information
            """
            if not self.tool_manager:
                return json.dumps({"error": "Tool manager not available"})
                
            tools_info = self.tool_manager.list_tools()
            tools = tools_info.get("tools", {})
            
            if script_name not in tools:
                return json.dumps({"error": f"Script '{script_name}' not found"})
                
            return json.dumps(tools[script_name], indent=2)
        
        def update_script_tool(script_name: str, updates_json: str) -> str:
            """
            Update an existing script
            
            Args:
                script_name: Name of the script to update
                updates_json: JSON string of updates
                
            Returns:
                Status message
            """
            return self.update_script(script_name, updates_json)
        
        def remove_script_tool(script_name: str) -> str:
            """
            Remove a script
            
            Args:
                script_name: Name of the script to remove
                
            Returns:
                Status message
            """
            return self.remove_script(script_name)

        return Agent(
            name="Factorio Lua Coding Agent",
            handoff_description="Specialist agent for Factorio Lua script generation and automation",
            instructions=system_prompt,
            model=config["openai"]["MODEL"],
            tools=[
                query_wiki_knowledge_base,
                query_api_knowledge_base,
                function_tool(save_generated_lua_script),
                function_tool(list_available_scripts_tool),
                function_tool(get_script_info_tool),
                function_tool(update_script_tool),
                function_tool(remove_script_tool),
            ],
        )
    
    def save_lua_script(self, script_name: str, lua_code: str, description: str, parameters_json: str = "{}", version: str = "1.0.0") -> str:
        """
        Save a generated Lua script using the UnifiedToolManager
        
        Args:
            script_name: Name for the script
            lua_code: The complete Lua script code (including /sc prefix)
            description: Description of what the script does  
            parameters_json: JSON string of parameters (optional)
            version: Version of the script
        Returns:
            Status message indicating success or failure
        """
        try:
            # Parse parameters from JSON
            try:
                parameters = json.loads(parameters_json) if parameters_json else {}
            except json.JSONDecodeError:
                return f"Invalid parameters JSON format: {parameters_json}"
            
            # Validate the generated script
            validation_result = self.validate_lua_code(lua_code)
            if not validation_result['valid']:
                return f"Lua script validation failed: {validation_result['errors']}"
            
            # Check if script already exists through tool manager
            if not self.tool_manager:
                return "Tool manager not available"
                
            existing_tools = self.tool_manager.list_tools()
            if script_name in existing_tools.get("tools", {}):
                return f"Script '{script_name}' already exists. Use update_script_tool to modify it."
            
            # Save files locally
            script_file = self.tools_dir / f"{script_name}.lua"
            with open(script_file, 'w') as f:
                f.write(lua_code)
            
            # Generate Python wrapper
            python_wrapper = self.generate_python_wrapper(script_name, description, parameters, lua_code)
            wrapper_file = self.tools_dir / f"{script_name}.py"
            with open(wrapper_file, 'w') as f:
                f.write(python_wrapper)
            
            # Register with tool manager
            tool_metadata = {
                'description': description,
                'parameters': parameters,
                'api_requirements': [],
                'created_at': datetime.now().isoformat(),
                'version': version,
                'lua_file_path': str(script_file),
                'python_file_path': str(wrapper_file),
            }
            
            # Save to unified registry through tool manager
            self.tool_manager.register_generated_tool(script_name, tool_metadata)
            
            self.logger.info(f"Successfully saved Lua script: {script_name}")
            return f"Successfully saved Factorio Lua script '{script_name}' with Python wrapper to {script_file}"
            
        except Exception as e:
            self.logger.error(f"Failed to save script {script_name}: {e}")
            return f"Failed to save script: {str(e)}"
    
    def generate_python_wrapper(self, 
                                script_name: str,
                                description: str,
                                parameters: Dict[str, str],
                                lua_script: str) -> str:
        """
        Generate Python wrapper for the parameterized Lua script
        
        Args:
            script_name: Name of the script
            description: Script description
            parameters: Parameter specifications (name -> description)
            lua_script: The Lua script template with placeholders
        Returns:
            Generated Python wrapper code
        """
        
        # Generate parameter list for function signature
        param_list = ", ".join([f"{name}: str" for name in parameters.keys()])
        
        # Generate parameter documentation
        param_docs = "\n".join([f"        {name}: {desc}" 
                               for name, desc in parameters.items()])   
        
        # Generate parameter replacement code
        param_replacement_code = ""
        if parameters:
            param_replacement_code = """
        # Replace parameters in the Lua script template
        script_to_execute = lua_script_template"""
            
            for param_name in parameters.keys():
                param_replacement_code += f"""
        script_to_execute = script_to_execute.replace("{{{param_name}}}", str({param_name}))"""
        else:
            param_replacement_code = """
        # No parameters to replace
        script_to_execute = lua_script_template"""
                
        # Build the parameter dict for the result
        param_dict_str = ", ".join([f'"{name}": {name}' for name in parameters.keys()])
        
        # Escape the lua script for inclusion in Python string
        escaped_lua_script = lua_script.replace('"""', '"'*3).replace('\\', '\\\\')
        
        # Count placeholders for metadata
        placeholder_count = len([p for p in lua_script.split('{') if '}' in p])
        
        # Generate wrapper code
        wrapper_template = '''"""
{description}

This is a dynamically generated Python wrapper for a parameterized Factorio Lua script.
Generated at: {timestamp}
"""
from typing import Dict, Any
from api.factorio_interface import FactorioInterface
import toml

# Global variables for lazy loading
_factorio_interface = None
_config = None

def get_factorio_interface(description: str = ""):
    """Get the factorio interface instance, creating it if necessary"""
    global _factorio_interface, _config
    
    if _factorio_interface is None:
        if _config is None:
            _config = toml.load("config/config.toml")
        _factorio_interface = FactorioInterface(
            _config["rcon"]["host"], 
            _config["rcon"]["port"], 
            _config["rcon"]["password"],
            message=description
        )
    
    return _factorio_interface

def {script_name}({param_list}) -> Dict[str, Any]:
    """
    {description}
    
    Args:{param_docs}
        
    Returns:
        Dict containing operation results and status information
    """
    try:
        # The Lua script template with placeholders
        lua_script_template = """{escaped_lua_script}"""
        {param_replacement_code}
        
        # Execute the parameterized Lua script via RCON
        factorio = get_factorio_interface(description="{description}")
        output = factorio._send_command(script_to_execute)
        
        result = {{
            "executed": True,
            "output": output,
            "script_name": "{script_name}",
            "parameters": {{{param_dict_str}}},
        }}
        
        return result
        
    except Exception as e:
        return {{
            "executed": False,
            "message": f"Script execution failed: {{str(e)}}",
            "error": str(e),
            "script_name": "{script_name}",
            "parameters": {{{param_dict_str}}}
        }}


# Script metadata for registry
SCRIPT_METADATA = {{
    "name": "{script_name}",
    "description": "{description}",
    "parameters": {parameters_json},
    "placeholder_count": {placeholder_count},
    "version": "{version}"
}}
'''.format(
            description=description,
            timestamp=datetime.now().isoformat(),
            script_name=script_name,
            param_list=param_list,
            param_docs=param_docs if param_docs else "\n        No parameters required",
            escaped_lua_script=escaped_lua_script,
            param_replacement_code=param_replacement_code,
            param_dict_str=param_dict_str,
            parameters_json=json.dumps(parameters),
            placeholder_count=placeholder_count,
            version=version
        )
        
        return wrapper_template
    
    def validate_lua_code(self, lua_code: str) -> Dict[str, Any]:
        """
        Validate the generated Lua code using lupa if available
        
        Args:
            lua_code: Lua script code to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Remove /sc prefix for validation
            clean_code = lua_code.strip()
            if clean_code.startswith('/sc'):
                clean_code = clean_code[3:].strip()
            
            if self.lua_runtime:
                try:
                    # Try to load the code (doesn't execute, just parses)
                    self.lua_runtime.eval(f"function() {clean_code} end")
                    self.logger.info("Lua syntax validation passed")
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Lua syntax error: {str(e)}")
            else:
                validation_result["warnings"].append("Lua runtime not available, skipping syntax validation")
            
            return validation_result
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            return validation_result
     
    def get_available_scripts_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available scripts from the unified tool manager
        
        Returns:
            List of script information dictionaries
        """
        if not self.tool_manager:
            return []
            
        tools_info = self.tool_manager.list_tools()
        tools = tools_info.get("tools", {})
        
        scripts_list = []
        for tool_name, tool_info in tools.items():
            provider_result = tool_info.get("provider_result", {})
            script_info = provider_result.get("script_info", {})
            
            scripts_list.append({
                'name': tool_name,
                'description': tool_info.get("metadata", {}).get("description", ""),
                'version': tool_info.get("metadata", {}).get("version", "1.0.0"),
                'created_at': tool_info.get("created_at", ""),
                'api_requirements': tool_info.get("metadata", {}).get("api_requirements", [])
            })
        
        return scripts_list
    
    def update_script(self, script_name: str, updates_json: str) -> str:
        """
        Update an existing script through the tool manager
        
        Args:
            script_name: Name of the script to update
            updates_json: JSON string of updates to apply
            
        Returns:
            Status message
        """
        if not self.tool_manager:
            return "Tool manager not available"
            
        try:
            # Parse updates from JSON
            try:
                updates = json.loads(updates_json)
            except json.JSONDecodeError:
                return f"Invalid updates JSON format: {updates_json}"
            
            # Delegate to tool manager
            result = self.tool_manager.update_tool_metadata(script_name, updates)
            return json.dumps(result)
            
        except Exception as e:
            return f"Failed to update script '{script_name}': {str(e)}"
    
    def remove_script(self, script_name: str) -> str:
        """
        Remove a script through the tool manager
        
        Args:
            script_name: Name of the script to remove
            
        Returns:
            Status message
        """
        if not self.tool_manager:
            return "Tool manager not available"
            
        try:
            result = self.tool_manager.remove_tool(script_name)
            return json.dumps(result)
            
        except Exception as e:
            return f"Failed to remove script '{script_name}': {str(e)}"
    
    async def run_interactive(self, input: str):
        """Run the coding agent in interactive mode"""
        self.logger.info("Starting Factorio Lua Coding Agent in interactive mode")
        try:
            await Runner.run(self.agent, input)
            
        except KeyboardInterrupt:
            self.logger.info("Coding Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Error in coding agent: {e}", exc_info=True)
        finally:
            self.logger.info("Coding Agent stopped")

async def main():
    """Main function for running the coding agent"""
    coding_agent = CodingAgent()
    input_str = input("Enter your input: ")
    await coding_agent.run_interactive(input_str)


if __name__ == "__main__":
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    asyncio.run(main())