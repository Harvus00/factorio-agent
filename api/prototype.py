"""
Factorio Prototype Definitions

This module provides comprehensive information about Factorio entities,
items, recipes and their relationships.
"""

# 实体类型定义
ENTITY_TYPES = {
    "production": ["assembling-machine", "furnace", "mining-drill"],
    "logistics": ["transport-belt", "splitter", "underground-belt", "inserter", "chest"],
    "energy": ["boiler", "steam-engine", "solar-panel", "accumulator", "electric-pole"],
    "defense": ["wall", "turret", "gate"],
    "other": ["lab", "pipe", "pipe-to-ground", "offshore-pump"]
}

# 实体详细信息
ENTITIES = {
    "stone-furnace": {
        "type": "furnace",
        "crafting_categories": ["smelting"],
        "energy_source": "burner",
        "energy_usage": "90kW",
        "crafting_speed": 1.0
    },
    "burner-mining-drill": {
        "type": "mining-drill",
        "resource_categories": ["basic-solid"],
        "energy_source": "burner",
        "energy_usage": "150kW",
        "mining_speed": 0.25
    },
    "assembling-machine-1": {
        "type": "assembling-machine",
        "crafting_categories": ["crafting"],
        "energy_source": "electric",
        "energy_usage": "75kW",
        "crafting_speed": 0.5
    },
    "burner-inserter": {
        "type": "inserter",
        "energy_source": "burner",
        "energy_usage": "188kW",
        "rotation_speed": 0.03125
    },
    "transport-belt": {
        "type": "transport-belt",
        "speed": 0.03125
    },
    "wooden-chest": {
        "type": "chest",
        "inventory_size": 16
    },
    "iron-chest": {
        "type": "chest",
        "inventory_size": 32
    },
    "steel-chest": {
        "type": "chest",
        "inventory_size": 48
    },
    "small-electric-pole": {
        "type": "electric-pole",
        "supply_area_distance": 2.5,
        "wire_reach_distance": 5.0
    },
    "medium-electric-pole": {
        "type": "electric-pole",
        "supply_area_distance": 3.5,
        "wire_reach_distance": 7.5
    },
    "big-electric-pole": {
        "type": "electric-pole",
        "supply_area_distance": 2.0,
        "wire_reach_distance": 30.0
    },
    "pipe": {
        "type": "pipe",
        "fluid_capacity": 100
    },
    "pipe-to-ground": {
        "type": "pipe-to-ground",
        "fluid_capacity": 100,
        "max_distance": 10
    },
    "boiler": {
        "type": "boiler",
        "energy_source": "burner",
        "energy_consumption": "1.8MW"
    },
    "steam-engine": {
        "type": "generator",
        "fluid_usage": 30,
        "max_power": "900kW"
    },
    "offshore-pump": {
        "type": "offshore-pump",
        "pumping_speed": 1200
    },
    "lab": {
        "type": "lab",
        "energy_usage": "60kW",
        "researching_speed": 1
    }
}

# 物品详细信息
ITEMS = {
    "iron-plate": {
        "stack_size": 100,
        "fuel_value": None
    },
    "copper-plate": {
        "stack_size": 100,
        "fuel_value": None
    },
    "iron-ore": {
        "stack_size": 50,
        "fuel_value": None
    },
    "copper-ore": {
        "stack_size": 50,
        "fuel_value": None
    },
    "coal": {
        "stack_size": 50,
        "fuel_value": "8MJ"
    },
    "stone": {
        "stack_size": 50,
        "fuel_value": None
    },
    "wood": {
        "stack_size": 100,
        "fuel_value": "4MJ"
    },
    "iron-gear-wheel": {
        "stack_size": 100,
        "fuel_value": None
    },
    "electronic-circuit": {
        "stack_size": 200,
        "fuel_value": None
    },
    "advanced-circuit": {
        "stack_size": 200,
        "fuel_value": None
    },
    "steel-plate": {
        "stack_size": 100,
        "fuel_value": None
    },
    "stone-brick": {
        "stack_size": 100,
        "fuel_value": None
    },
    "copper-cable": {
        "stack_size": 200,
        "fuel_value": None
    }
}

# 配方信息
RECIPES = {
    "iron-gear-wheel": {
        "ingredients": [{"iron-plate": 2}],
        "result": "iron-gear-wheel",
        "result_count": 1,
        "energy_required": 0.5,
        "category": "crafting"
    },
    "electronic-circuit": {
        "ingredients": [{"iron-plate": 1}, {"copper-cable": 3}],
        "result": "electronic-circuit",
        "result_count": 1,
        "energy_required": 0.5,
        "category": "crafting"
    },
    "copper-cable": {
        "ingredients": [{"copper-plate": 1}],
        "result": "copper-cable",
        "result_count": 2,
        "energy_required": 0.5,
        "category": "crafting"
    },
    "iron-plate": {
        "ingredients": [{"iron-ore": 1}],
        "result": "iron-plate",
        "result_count": 1,
        "energy_required": 3.2,
        "category": "smelting"
    },
    "copper-plate": {
        "ingredients": [{"copper-ore": 1}],
        "result": "copper-plate",
        "result_count": 1,
        "energy_required": 3.2,
        "category": "smelting"
    },
    "steel-plate": {
        "ingredients": [{"iron-plate": 5}],
        "result": "steel-plate",
        "result_count": 1,
        "energy_required": 16,
        "category": "smelting"
    },
    "stone-brick": {
        "ingredients": [{"stone": 2}],
        "result": "stone-brick",
        "result_count": 1,
        "energy_required": 3.2,
        "category": "smelting"
    },
    "burner-mining-drill": {
        "ingredients": [{"iron-gear-wheel": 3}, {"stone-furnace": 1}, {"iron-plate": 3}],
        "result": "burner-mining-drill",
        "result_count": 1,
        "energy_required": 2,
        "category": "crafting"
    },
    "stone-furnace": {
        "ingredients": [{"stone": 5}],
        "result": "stone-furnace",
        "result_count": 1,
        "energy_required": 0.5,
        "category": "crafting"
    }
}

def get_entity_names():
    """获取所有有效的实体名称列表"""
    return list(ENTITIES.keys())

def get_entity_by_type(entity_type):
    """获取指定类型的所有实体"""
    return [name for name, data in ENTITIES.items() if data["type"] == entity_type]

def get_item_names():
    """获取所有有效的物品名称列表"""
    return list(ITEMS.keys())

def get_recipe_names():
    """获取所有有效的配方名称列表"""
    return list(RECIPES.keys())

def get_recipe_for_item(item_name):
    """获取制作指定物品的配方"""
    for recipe_name, recipe in RECIPES.items():
        if recipe["result"] == item_name:
            return recipe
    return None

def get_entity_info(entity_name):
    """获取实体的详细信息"""
    return ENTITIES.get(entity_name)

def get_item_info(item_name):
    """获取物品的详细信息"""
    return ITEMS.get(item_name)

def is_valid_entity(name):
    """检查实体名称是否有效"""
    return name in ENTITIES

def is_valid_item(name):
    """检查物品名称是否有效"""
    return name in ITEMS