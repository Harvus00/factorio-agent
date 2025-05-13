import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.factorio_interface import FactorioInterface

# 创建全局接口实例
try:
    factorio = FactorioInterface()
except Exception as e:
    print(f"FactorioInterface init failed: {e}")
    sys.exit(1)

# 测试移动玩家
# result = factorio.move_player(1, 1)
# print(f"移动玩家结果: {result}")

# # 测试获取玩家位置
# position = factorio.get_player_position()
# print(f"玩家位置: {position}")

# result = factorio.place_entity("burner-miner", 30, 10)
# print(f"放置矿工结果: {result}")

# result = factorio.list_supported_entities(mode="search", keyword="inserter")
# print(f"Search result: {result}")

# result = factorio.find_surface_tile(position_x=-64, position_y=36, radius=2,limit=15)
# print(f"Find surface tile result: {result}")

# result = factorio.place_entity("offshore-pump", -60, 36)
# print(f"Place offshore pump result: {result}")

result = factorio.search_entities(name="burner-inserter", position_x=-60, position_y=36, radius=5)
print(f"Search entities result: {result}")

# result = factorio.search_entities(name="offshore-pump", position_x=-60, position_y=36, radius=5)
# print(f"Search entities result: {result}")