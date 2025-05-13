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

result = factorio.place_entity("burner-mining-drill", 10, 10)
print(f"result: {result}")

# result = factorio.list_supported_entities(mode="search", keyword="inserter")
# print(f"Search result: {result}")

result = factorio.find_surface_tile(position_x=-50, position_y=27, radius=2)
print(f"Find surface tile result: {result}")

# result = factorio.place_entity("offshore-pump", -60, 36)
# print(f"Place offshore pump result: {result}")

# result = factorio.search_entities(name="coal", limit=2)
# print(f"Search entities result: {result}")

# result = factorio.search_entities(name="offshore-pump", position_x=-60, position_y=36, radius=5)
# print(f"Search entities result: {result}")