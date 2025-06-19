/c
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
