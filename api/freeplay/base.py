class FactorioAPI:
    class Player:
        @staticmethod
        def get_position():
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
        def place(name: str, x: float, y: float, direction: float = 0):
            """Place an entity in the game.
            Args:
                name: The entity prototype name to create.
                x: the x coordinate of the entity
                y: the y coordinate of the entity
                direction: the direction of the entity (default 0) 0, 4, 8, 12 means up, right, down, left
            """
            # surface.can_place_entity checks according to the entity's collision box, while player.can_place_entity checks according to the player's reach distance and some other factors.
            return f"""
            /c local player = game.get_player(1)
            if player.get_main_inventory().get_item_count('{name}') > 0 and game.surfaces[1].can_place_entity{{name='{name}', position={{{x},{y}}}}} and player.can_place_entity{{name='{name}', position={{{x},{y}}}}} then
                game.surfaces[1].create_entity{{name='{name}', position={{x={x}, y={y}}},direction= {direction}, force=game.forces.player}}    
                rcon.print('Entity placed')        
            else
                rcon.print('Cannot place entity')
            end
            """
        # def place(name: str, x: float, y: float, direction: float = 0):
        #     """Place an entity in the game.
        #     Args:
        #         name: The entity prototype name to create.
        #         x: the x coordinate of the entity
        #         y: the y coordinate of the entity
        #         direction: the direction of the entity (default 0) 0, 4, 8, 12 means up, right, down, left
        #     """
        #     # surface.can_place_entity checks according to the entity's collision box, while player.can_place_entity checks according to the player's reach distance and some other factors.
        #     return f"""
        #     /c local player = game.get_player(1)
        #     if player.get_main_inventory().get_item_count('{name}') > 0 and game.surfaces[1].can_place_entity{{name='{name}', position={{{x},{y}}}}} and player.can_place_entity{{name='{name}', position={{{x},{y}}}}} then
        #         game.surfaces[1].create_entity{{name='{name}', position={{x={x}, y={y}}},direction= {direction}, force=game.forces.player}}    
        #         player.get_main_inventory().remove({{name='{name}', count=1}})
        #         rcon.print('Entity placed')        
        #     else
        #         rcon.print('Cannot place entity')
        #     end
        #     """
        
        @staticmethod
        def remove(name: str, x: float, y: float):
            """Remove an entity in the game.
            Args:
                name: The entity prototype name to remove.
                x: the x coordinate of the entity
                y: the y coordinate of the entity"""
            return f"""
            /c local entity = game.surfaces[1].find_entity('{name}', {{{x},{y}}}) 
            if entity and game.get_player(1).can_reach_entity(entity) then 
            entity.destroy() rcon.print('Entity removed')
            elseif not entity then rcon.print('Entity not found')
            else rcon.print('Cannot reach entity')
            end
            """
        # def remove(name: str, x: float, y: float):
        #     """Remove an entity in the game.
        #     Args:
        #         name: The entity prototype name to remove.
        #         x: the x coordinate of the entity
        #         y: the y coordinate of the entity"""
        #     return f"""
        #     /c local entity = game.surfaces[1].find_entity('{name}', {{{x},{y}}}) 
        #     if entity and game.get_player(1).can_reach_entity(entity) then 
        #     entity.destroy() rcon.print('Entity removed')
        #     game.get_player(1).get_main_inventory().insert({{name='{name}', count=1}})
        #     elseif not entity then rcon.print('Entity not found')
        #     else rcon.print('Cannot reach entity')
        #     end
        #     """

    class Inventory:
        @staticmethod
        def add_item(entity: str, item: str, count: int, x: float = None, y: float = None):
            if entity == "player":
                return f"/c game.get_player(1).get_main_inventory().insert{{name='{item}', count={count}}}"
            else:
                return f"""
                /c local entity = game.surfaces[1].find_entity('{entity}', {{{x},{y}}})
                if entity then
                    entity.get_inventory(1).insert{{name='{item}', count={count}}}
                    rcon.print('Item added')
                else
                    rcon.print('Entity not found')
                end
                """
        
        @staticmethod
        def remove_item(entity: str, item: str, count: int, x: float = None, y: float = None):
            if entity == "player":
                return f"/c game.get_player(1).get_main_inventory().remove({{name='{item}', count={count}}})"
            else:
                return f"""
                /c local entity = game.surfaces[1].find_entity('{entity}', {{{x},{y}}})
                if entity then
                    entity.get_inventory(1).remove{{name='{item}', count={count}}}
                    rcon.print('Item removed')
                else
                    rcon.print('Entity not found')
                end
                """