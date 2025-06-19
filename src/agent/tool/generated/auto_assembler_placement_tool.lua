/c
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
