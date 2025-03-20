import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.factorio_interface import FactorioInterface

# 创建全局接口实例
factorio = FactorioInterface()

# 测试移动玩家
result = factorio.move_player(1, 1)
print(f"移动玩家结果: {result}")

# 测试获取玩家位置
position = factorio.get_player_position()
print(f"玩家位置: {position}")

# 测试获取可用原型
prototypes = factorio.get_available_prototypes()
print(f"可用原型: {prototypes}")