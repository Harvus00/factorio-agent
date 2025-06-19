"""
Inserts one unit of wood into the fuel inventory of a burner mining drill at specified coordinates.

This is a dynamically generated Python wrapper for a parameterized Factorio Lua script.
Generated at: 2025-06-19T15:14:53.139821
"""
from typing import Dict, Any
from api.factorio_interface import FactorioInterface
import toml

# Global variables for lazy loading
_factorio_interface = None
_config = None

def get_factorio_interface():
    """Get the factorio interface instance, creating it if necessary"""
    global _factorio_interface, _config
    
    if _factorio_interface is None:
        if _config is None:
            _config = toml.load("config/config.toml")
        _factorio_interface = FactorioInterface(
            _config["rcon"]["host"], 
            _config["rcon"]["port"], 
            _config["rcon"]["password"]
        )
    
    return _factorio_interface

def insert_wood_into_mining_drill(x_position: str, y_position: str) -> Dict[str, Any]:
    """
    Inserts one unit of wood into the fuel inventory of a burner mining drill at specified coordinates.
    
    Args:        x_position: number
        y_position: number
        
    Returns:
        Dict containing operation results and status information
    """
    try:
        # The Lua script template with placeholders
        lua_script_template = """/c
-- Insert one unit of wood into the fuel inventory of a burner mining drill at specified coordinates
-- Parameters: x_position, y_position

local surface = game.surfaces[1]
local x = {x_position} -- e.g., 0
local y = {y_position} -- e.g., 0

local entity = surface.find_entity("burner-mining-drill", {x = x, y = y})
if not entity then
    rcon.print("Error: No burner mining drill found at position (" .. x .. ", " .. y .. ")")
    return
end

local fuel_inv = entity.get_fuel_inventory()
if not fuel_inv then
    rcon.print("Error: Entity at position (" .. x .. ", " .. y .. ") does not have a fuel inventory")
    return
end

local inserted = fuel_inv.insert({name = "wood", count = 1})
if inserted > 0 then
    rcon.print("Successfully inserted 1 wood into burner mining drill at position (" .. x .. ", " .. y .. ")")
else
    rcon.print("Failed to insert wood; burner mining drill fuel inventory might be full")
end
"""
        
                # Replace parameters in the Lua script template
        script_to_execute = lua_script_template
        script_to_execute = script_to_execute.replace("{x_position}", str(x_position))
        script_to_execute = script_to_execute.replace("{y_position}", str(y_position))
        
        # Execute the parameterized Lua script via RCON
        factorio = get_factorio_interface()
        success, output = factorio.execute_command(script_to_execute)
        
        result = {
            "success": success,
            "message": "Script executed successfully" if success else "Script execution failed",
            "output": output,
            "script_name": "insert_wood_into_mining_drill",
            "parameters": {"x_position": x_position, "y_position": y_position},
            "executed_script": script_to_execute[:200] + "..." if len(script_to_execute) > 200 else script_to_execute
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Script execution failed: {str(e)}",
            "error": str(e),
            "script_name": "insert_wood_into_mining_drill",
            "parameters": {"x_position": x_position, "y_position": y_position}
        }


# Script metadata for registry
SCRIPT_METADATA = {
    "name": "insert_wood_into_mining_drill",
    "description": "Inserts one unit of wood into the fuel inventory of a burner mining drill at specified coordinates.",
    "parameters": {"x_position": "number", "y_position": "number"},
    "script_type": "factorio_lua_parameterized",
    "version": "1.0.0",
    "is_parameterized": True,
    "placeholder_count": 4
}
