"""
Automatically places assemblers in a configurable grid around the player.

This is a dynamically generated Python wrapper for a parameterized Factorio Lua script.
Generated at: 2025-06-19T15:13:16.727922
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

def auto_assembler_placement_tool(assembler_name: str, grid_width: str, grid_height: str, spacing: str) -> Dict[str, Any]:
    """
    Automatically places assemblers in a configurable grid around the player.
    
    Args:        assembler_name: assembling-machine-1
        grid_width: 5
        grid_height: 3
        spacing: 3
        
    Returns:
        Dict containing operation results and status information
    """
    try:
        # The Lua script template with placeholders
        lua_script_template = """/c
-- Automatically place assemblers in a specified rectangular grid around the player
-- Parameters:
-- assembler_name: string, e.g., "assembling-machine-1"
-- grid_width: integer, number of assemblers placed along X-axis (default 5)
-- grid_height: integer, number of assemblers placed along Y-axis (default 3)
-- spacing: number, distance in tiles between assemblers (default 3)

local player = game.players[1]

if not player then
    rcon.print("Error: No player found")
    return
end

local surface = player.surface

local assembler_name = "{assembler_name}" -- e.g., "assembling-machine-1", "assembling-machine-2"
local grid_width = {grid_width} -- typically 5
local grid_height = {grid_height} -- typically 3
local spacing = {spacing} -- e.g., 3

if not game.entity_prototypes[assembler_name] then
    rcon.print("Error: Invalid assembler name: " .. assembler_name)
    return
end

local start_position = player.position

-- Calculate start position offset so grid is centered around player
local offset_x = -((grid_width - 1) * spacing) / 2
local offset_y = -((grid_height - 1) * spacing) / 2

local placed_count = 0

for row=0, grid_height-1 do
    for col=0, grid_width-1 do
        local pos = {x = start_position.x + offset_x + col * spacing, y = start_position.y + offset_y + row * spacing}
        -- Check if position is buildable
        local can_build = surface.can_place_entity{name=assembler_name, position=pos, force=player.force}
        if can_build then
            surface.create_entity{name=assembler_name, position=pos, force=player.force}
            placed_count = placed_count + 1
        end
    end
end

rcon.print("Placed " .. placed_count .. " " .. assembler_name .. " entities around player.")
"""
        
                # Replace parameters in the Lua script template
        script_to_execute = lua_script_template
        script_to_execute = script_to_execute.replace("{assembler_name}", str(assembler_name))
        script_to_execute = script_to_execute.replace("{grid_width}", str(grid_width))
        script_to_execute = script_to_execute.replace("{grid_height}", str(grid_height))
        script_to_execute = script_to_execute.replace("{spacing}", str(spacing))
        
        # Execute the parameterized Lua script via RCON
        factorio = get_factorio_interface()
        success, output = factorio.execute_command(script_to_execute)
        
        result = {
            "success": success,
            "message": "Script executed successfully" if success else "Script execution failed",
            "output": output,
            "script_name": "auto_assembler_placement_tool",
            "parameters": {"assembler_name": assembler_name, "grid_width": grid_width, "grid_height": grid_height, "spacing": spacing},
            "executed_script": script_to_execute[:200] + "..." if len(script_to_execute) > 200 else script_to_execute
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Script execution failed: {str(e)}",
            "error": str(e),
            "script_name": "auto_assembler_placement_tool",
            "parameters": {"assembler_name": assembler_name, "grid_width": grid_width, "grid_height": grid_height, "spacing": spacing}
        }


# Script metadata for registry
SCRIPT_METADATA = {
    "name": "auto_assembler_placement_tool",
    "description": "Automatically places assemblers in a configurable grid around the player.",
    "parameters": {"assembler_name": "assembling-machine-1", "grid_width": 5, "grid_height": 3, "spacing": 3},
    "script_type": "factorio_lua_parameterized",
    "version": "1.0.0",
    "is_parameterized": True,
    "placeholder_count": 7
}
