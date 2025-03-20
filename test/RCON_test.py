import factorio_rcon
from api.sandbox.base import FactorioAPI

client = factorio_rcon.RCONClient("127.0.0.1", 8088, "lvshrd")
# response = client.send_command("/help")

"""
("stone-furnace",-25, 12)
("burner-mining-drill", -25, 10)
("assembling-machine-1", -20, 10)
("burner-inserter", -19.5, 15.5)
"""

# response = client.send_command(FactorioAPI.Player.move_to(0, 0))
# response = client.send_command(FactorioAPI.Entity.place("burner-mining-drill", -25, 10))
# response = client.send_command(FactorioAPI.Entity.remove("stone-furnace",-25, 12))
# response = client.send_command(FactorioAPI.Inventory.insert_item("burner-inserter",1)+ FactorioAPI.Entity.place("burner-inserter", -20, 15)[3:])
# response = client.send_command(FactorioAPI.Inventory.insert_item("coal",1,"burner-inserter", -19.5, 15.5))

# response = client.send_command(FactorioAPI.Entity.place("assembling-machine-1", -20, 10))
# response = client.send_command(FactorioAPI.Inventory.insert_item("iron-ore",1,"stone-furnace",-25, 12))
# response = client.send_command(FactorioAPI.Inventory.remove_item("coal",2))
# response = client.send_command(FactorioAPI.Entity.get_entities(name="burner-inserter"))
response = client.send_command(FactorioAPI.Inventory.insert_item("iron-ore",2,"fuel","stone-furnace",-25, 12))

print(f"RCON response: {response if response else 'ERROR'}")