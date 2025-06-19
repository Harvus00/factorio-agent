"""
Inserts specified fuel into a burner mining drill located at given coordinates (x, y) on the main surface.

This is a dynamically generated Python wrapper for a parameterized Factorio Lua script.
Generated at: 2025-06-19T15:14:30.290479
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

def insert_fuel_into_mining_drill(x_position: str, y_position: str, fuel_item_name: str, fuel_quantity: str) -> Dict[str, Any]:
    """
    Inserts specified fuel into a burner mining drill located at given coordinates (x, y) on the main surface.
    
    Args:        x_position: number
        y_position: number
        fuel_item_name: string
        fuel_quantity: number
        
    Returns:
        Dict containing operation results and status information
    """
    try:
        # The Lua script template with placeholders
        lua_script_template = """/c
-- Insert specified fuel into burner mining drill at given coordinates
-- Parameters: x={x_position}, y={y_position}, fuel_item={fuel_item_name}, fuel_amount={fuel_quantity}
local surface = game.surfaces[1] -- Assuming main surface
local x = {x_position} -- e.g., 0
local y = {y_position} -- e.g., 0
local fuel_item = "{fuel_item_name}" -- e.g., "coal"
local fuel_amount = {fuel_quantity} -- e.g., 10

local drill = surface.find_entity("burner-mining-drill", {x=x, y=y})

if not drill then
    rcon.print("Error: No burner mining drill found at position (" .. x .. ", " .. y .. ")")
    return
end

if not drill.burner then
    rcon.print("Error: Entity at position is not a burner fuel entity")
    return
end

local inserted = drill.burner.inventory.insert({name=fuel_item, count=fuel_amount})

if inserted > 0 then
    rcon.print("Inserted " .. inserted .. " " .. fuel_item .. " into burner mining drill at (" .. x .. ", " .. y .. ")")
else
    rcon.print("Failed to insert fuel - inventory full or invalid fuel item")
end
"""
        
                # Replace parameters in the Lua script template
        script_to_execute = lua_script_template
        script_to_execute = script_to_execute.replace("{x_position}", str(x_position))
        script_to_execute = script_to_execute.replace("{y_position}", str(y_position))
        script_to_execute = script_to_execute.replace("{fuel_item_name}", str(fuel_item_name))
        script_to_execute = script_to_execute.replace("{fuel_quantity}", str(fuel_quantity))
        
        # Execute the parameterized Lua script via RCON
        factorio = get_factorio_interface()
        success, output = factorio.execute_command(script_to_execute)
        
        result = {
            "success": success,
            "message": "Script executed successfully" if success else "Script execution failed",
            "output": output,
            "script_name": "insert_fuel_into_mining_drill",
            "parameters": {"x_position": x_position, "y_position": y_position, "fuel_item_name": fuel_item_name, "fuel_quantity": fuel_quantity},
            "executed_script": script_to_execute[:200] + "..." if len(script_to_execute) > 200 else script_to_execute
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Script execution failed: {str(e)}",
            "error": str(e),
            "script_name": "insert_fuel_into_mining_drill",
            "parameters": {"x_position": x_position, "y_position": y_position, "fuel_item_name": fuel_item_name, "fuel_quantity": fuel_quantity}
        }


# Script metadata for registry
SCRIPT_METADATA = {
    "name": "insert_fuel_into_mining_drill",
    "description": "Inserts specified fuel into a burner mining drill located at given coordinates (x, y) on the main surface.",
    "parameters": {"x_position": "number", "y_position": "number", "fuel_item_name": "string", "fuel_quantity": "number"},
    "script_type": "factorio_lua_parameterized",
    "version": "1.0.0",
    "is_parameterized": True,
    "placeholder_count": 10
}
