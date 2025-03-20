"""
Factorio Prototype Lists

This module provides lists of valid entity and item names in Factorio,
as well as utility functions to check if a name is valid.
"""

# 实体名称列表
ENTITY_NAMES = [
    "stone-furnace",
    "burner-mining-drill",
    "assembling-machine-1",
    "burner-inserter",
    "transport-belt",
    "wooden-chest",
    "iron-chest",
    "steel-chest",
    "small-electric-pole",
    "medium-electric-pole",
    "big-electric-pole",
    "pipe",
    "pipe-to-ground",
    "boiler",
    "steam-engine",
    "offshore-pump",
    "lab",
    # 可以根据需要添加更多实体
]

# 物品名称列表
ITEM_NAMES = [
    "iron-plate",
    "copper-plate",
    "iron-ore",
    "copper-ore",
    "coal",
    "stone",
    "wood",
    "iron-gear-wheel",
    "electronic-circuit",
    "advanced-circuit",
    "steel-plate",
    "stone-brick",
    "copper-cable",
    # 可以根据需要添加更多物品
]

def get_entity_names():
    """获取所有有效的实体名称列表"""
    return ENTITY_NAMES

def get_item_names():
    """获取所有有效的物品名称列表"""
    return ITEM_NAMES

def is_valid_entity(name):
    """检查实体名称是否有效"""
    return name in ENTITY_NAMES

def is_valid_item(name):
    """检查物品名称是否有效"""
    return name in ITEM_NAMES