/c
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
