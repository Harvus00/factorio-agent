class FactorioAPI:
    class Player:
        @staticmethod
        def get_player_position():
            """Get the player's current position."""
            return "/c rcon.print(game.get_player(1).position)"
        
        @staticmethod
        def move_to(x: float, y: float):
            """Move the player to a specific position.
            Args:
                x: the x coordinate of the player
                y: the y coordinate of the player
            """
            return f"/c game.get_player(1).teleport({{y = {y}, x = {x}}})"

    class Entity:
        @staticmethod
        def get_entities(bottom_left_x: float = None, bottom_left_y: float = None, top_right_x: float = None, top_right_y: float = None, position_x: float = None, position_y: float = None, radius: float = None, name: list = None, type: str = None, limit: int = None):
            """Find entities in the game based on specified filters.

            Args:
                bottom_left_x: The bottom-left x coordinate of the search area (optional).
                bottom_left_y: The bottom-left y coordinate of the search area (optional).
                top_right_x: The top-right x coordinate of the search area (optional).
                top_right_y: The top-right y coordinate of the search area (optional).
                position_x: The x coordinate of the center of the search circle (optional).
                position_y: The y coordinate of the center of the search circle (optional).
                radius: The radius of the search circle (optional).
                name: A list of entity prototype names to filter by (optional).
                type: The entity type to filter by (optional).
                limit: The maximum number of entities to return (optional).
            """
            filter_params = []
            if name:
                if isinstance(name, str):
                    filter_params.append(f"name = '{name}'")
                elif isinstance(name, list):
                    quoted_names = [f"'{n}'" for n in name]
                    filter_params.append(f"name = {{ {', '.join(quoted_names)} }}")
            if type:
                filter_params.append(f"type = '{type}'")
            if limit:
                filter_params.append(f"limit = {limit}")
            if bottom_left_x is not None and bottom_left_y is not None and top_right_x is not None and top_right_y is not None:
                filter_params.append(f"area={{ {{ {bottom_left_x}, {bottom_left_y} }}, {{ {top_right_x}, {top_right_y} }} }}")
            if position_x is not None and position_y is not None and radius is not None:
                filter_params.append(f"position={{ {position_x}, {position_y} }}, radius={radius}")
            filter_string = ", ".join(filter_params)

            return f"""/c local entities = game.surfaces[1].find_entities_filtered{{ {filter_string} }}
            if entities then
                local entity_data = {{}}
                for _, entity in ipairs(entities) do
                    table.insert(entity_data, {{name = entity.name, position = entity.position, type = entity.type}})
                end
                rcon.print(helpers.table_to_json(entity_data))
            else
                rcon.print('Failed: No entities found with the specified filters.')
            end
            """

        @staticmethod
        def place_entity(name: str, x: float, y: float, direction: int = 0):
            """Place an entity in the game.
            Args:
                name: The entity prototype name to create.
                x: the x coordinate of the entity
                y: the y coordinate of the entity
                direction: the direction of the entity (default 0) 0, 4, 8, 12 means up, right, down, left
            """
            inventory = FactorioAPI.Inventory
            # surface.can_place_entity checks according to the entity's collision box, while player.can_place_entity checks according to the player's reach distance and some other factors.
            return f"""/c local player = game.get_player(1)
            if  game.get_player(1).get_main_inventory().get_item_count('{name}') > 0 and game.surfaces[1].can_place_entity{{name='{name}', position={{{x},{y}}}}} and player.can_place_entity{{name='{name}', position={{{x},{y}}}}} then
                game.surfaces[1].create_entity{{name='{name}', position={{x={x}, y={y}}},direction= {direction}, force=game.forces.player}}    
                rcon.print('Success: Entity {name} placed')
                {inventory.remove_item(name,1)[3:]}
            else
                rcon.print('Failed: Cannot place entity {name}')
            end
            """
        
        @staticmethod
        def remove_entity(name: str, x: float, y: float):
            """Remove an entity in the game.
            Args:
                name: The entity prototype name to remove.
                x: the x coordinate of the entity
                y: the y coordinate of the entity"""
            inventory = FactorioAPI.Inventory
            return f"""/c local entity = game.surfaces[1].find_entity('{name}', {{{x},{y}}}) 
            if entity and game.get_player(1).can_reach_entity(entity) then 
            entity.destroy() rcon.print('Success: Entity {name} removed') {inventory.insert_item(name,1)[3:]}
            elseif not entity then rcon.print('Failed: Entity {name} not found')
            else rcon.print('Failed: Cannot reach {name}')
            end
            """

    class Inventory:
               
        # @staticmethod       
        # def get_available_inventory_types():
        #     inventory_types = [
        #     "fuel",
        #     # "burnt_result",
        #     "chest",
        #     # "logistic_container_trash",
        #     "furnace_source",
        #     "furnace_result",
        #     # "furnace_modules",
        #     "character_main",
        #     "character_guns",
        #     "character_ammo",
        #     "character_armor",
        #     # "character_vehicle",
        #     "character_trash",
        #     "assembling_machine_input",
        #     "assembling_machine_output",
        #     # "assembling_machine_modules",
        #     # "assembling_machine_dump"
        #     ]
        #     return inventory_types
        
        @staticmethod
        def insert_item(item: str, count: int,inventory_type: str = "character_main", entity: str = "player", x: float = None, y: float = None):
            """Insert certain numbers of items into entity, default insert into player main inventory.
            if into other entities inventory, specify the name and position of this entity
            Args:
                item: The item name to insert
                count: The count of the item
                entity(optional): The name of the entity to insert
                x(if entity specified): the x coordinate of the entity
                y(if entity specified): the y coordinate of the entity
                inventory_type(optional): the type of inventory to insert into.("fuel","chest","furnace_source","furnace_result","character_main","character_guns","character_ammo","character_armor","character_trash","assembling_machine_input","assembling_machine_output",)
            """
            if entity == "player":
                return f"/c game.get_player(1).get_inventory(defines.inventory.{inventory_type}).insert{{name='{item}', count={count}}} rcon.print('Success: {item} added to player {inventory_type}')"
            else:
                return f"""/c local entity = game.surfaces[1].find_entity('{entity}', {{{x},{y}}})
                if entity then
                    entity.get_inventory(defines.inventory.{inventory_type}).insert{{name='{item}', count={count}}}
                    rcon.print('Success: Item {item} added to {entity} {inventory_type}')
                else
                    rcon.print('Failed: Entity {entity} not found')
                end
                """
        
        @staticmethod
        def remove_item(item: str, count: int, entity: str = "player",x: float = None, y: float = None):
            """Remove certain numbers of items from entity, default remove from player main inventory.
            if from other entities inventory, specify the name and position of this entity
            Args:
                item: The item name to remove
                count: The count of the item
                entity(optional): The name of the entity to remove
                x: the x coordinate of the entity
                y: the y coordinate of the entity
            """
            if entity == "player":
                remove_item_from_player=f"""/c local main_inventory = game.get_player(1).get_main_inventory()
                if main_inventory.get_item_count('{item}') >= {count} then
                    main_inventory.remove({{name='{item}', count={count}}}) 
                    rcon.print('Success: {item} removed from player')
                else
                    rcon.print(string.format('Failed: %s count is %d', '{item}', main_inventory.get_item_count('{item}')))
                end
                """
                return remove_item_from_player
            else:
                remove_item_from_entity=f"""/c local entity = game.surfaces[1].find_entity('{entity}', {{{x},{y}}})
                if entity and entity.then
                    entity.get_inventory(1).remove{{name='{item}', count={count}}}
                    rcon.print('Item {item} removed')
                else
                    rcon.print('Entity {item} not found')
                end
                """
                return remove_item_from_entity
        
 
        @staticmethod
        def get_inventory(inventory_type: str, entity: str = "player", x: float = None, y: float = None):
            """Get inventory content from entity, default get player main inventory. 
            if from other entities inventory, specify the name and position of this entity
            Args:
                inventory_type: The type of inventory to get.("fuel","chest","furnace_source","furnace_result","character_main","character_guns","character_ammo","character_armor","character_trash","assembling_machine_input","assembling_machine_output",)
                entity(optional): The name of the entity to get.
                x: the x coordinate of the entity
                y: the y coordinate of the entity
            """
            if entity == "player":
                get_inventory_from_player = f"""/c local inventory = game.get_player(1).get_inventory(defines.inventory.{inventory_type})
                if inventory then
                    inventory_json=helpers.table_to_json(inventory.get_contents())
                    rcon.print(inventory_json)
                else
                    rcon.print('Failed: Inventory {inventory_type} not found for player.')
                end
                """
                return get_inventory_from_player
            else:
                get_inventory_from_entity = f"""/c local entity = game.surfaces[1].find_entity('{entity}', {{{x},{y}}})
                if entity then
                    local inventory = entity.get_inventory(defines.inventory.{inventory_type})
                    if inventory then
                        inventory_json=helpers.table_to_json(inventory.get_contents())
                        rcon.print(inventory_json)
                    else
                        rcon.print('Failed: Inventory {inventory_type} not found for {entity}.')
                    end
                else
                    rcon.print('Entity {entity} not found.')
                end
                """
                return get_inventory_from_entity
