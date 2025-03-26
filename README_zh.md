# Factorio Agent
[ [English](README.md) | [中文](README_zh.md) ]

一个基于人工智能的 Factorio 游戏代理，能够自主分析游戏状态并执行操作。

## 项目概述

Factorio Agent 是一个使用 OpenAI Agent SDK 构建的智能代理，它通过 RCON 协议与 Factorio 游戏服务器交互。该代理能够：

-   分析游戏状态（玩家位置、资源、库存等）
-   制定短期和长期策略
-   执行游戏操作（移动、建筑放置、资源收集等）
-   根据游戏变化自主调整计划

<p align="center">
  <img src="docs/game_demo.png" alt="Factorio agent play demo" width="40%">
  <img src="docs/action_log.png" alt="Factorio agent play demo" width="40%">
</p>

## 技术架构

-   **OpenAI API**: 提供人工智能决策能力
-   **RCON 协议**: 与 Factorio 服务器通信
-   **Python 异步编程**: 处理游戏交互和 AI 响应
-   **Factorio Runtime API**: 通过 Lua Factorio API 实现游戏操作工具函数

## 安装指南

### 前提条件

-   Python 3.11+
-   [Factorio 2.32](https://www.factorio.com/)
-   OpenAI API 密钥

### 安装步骤

1.  克隆仓库：

    ```bash
    git clone https://github.com/lvshrd/factorio-agent.git
    cd factorio-agent
    ```

2.  创建并激活虚拟环境：

    ```bash
    conda create -n factorio_agent_env python=3.11
    conda activate factorio_agent_env
    ```

3.  安装依赖：

    ```bash
    pip install -r requirements.txt
    ```

4.  配置：

    将 `config_example.toml` 重命名为 `config.toml`，并填写您的 OpenAI API 密钥和 Factorio 服务器信息：

    ```toml
    [openai]
    OPENAI_API_KEY = "your-api-key-here"

    [factorio]
    server_address = "localhost"
    rcon_port = 27015
    rcon_password = "your-rcon-password"

    [agent]
    max_steps = 100
    step_delay = 5
    ```

## 使用方法

1.  创建一个新的单人自由游戏，并确保 Factorio 服务器已启用 RCON（必要时，启动多人游戏，并在游戏[根目录](https://wiki.factorio.com/Application_directory) `./config/config.ini` 中配置 RCON 端口和密码）。

2.  首先执行任何命令以解锁成就限制。例如：运行测试脚本以确保 RCON 连接正常工作，并且代理可以访问 Factorio API。
    ```bash
    python test/RCON_test.py
    python test/interface_test.py
    ```

3.  运行代理：

    ```bash
    python main.py
    ```

4.  代理将开始分析游戏状态并执行操作。

## 项目结构

```
factorio-agent/
├── api/                      # API 相关代码
│   ├── __init__.py
│   ├── agent_tools.py        # 代理工具函数
│   ├── factorio_interface.py # Factorio 接口
│   ├── sandbox/              # 沙盒模式 API
│   │   └── base.py
│   └── prototype.py          # 游戏原型定义
├── test/                     # 测试代码
│   ├── __init__.py
│   ├── RCON_test.py
│   └── interface_test.py
├── config.toml               # 配置文件
├── main.py                   # 主程序
└── README_zh.md              # 项目文档
```

## 自定义和扩展

### 添加新工具

在 `api/agent_tools.py` 中添加新的工具函数：

```python
@function_tool
def your_new_tool(param1: str, param2: int) -> str:
    """
    工具函数描述

    Args:
        param1: 参数 1 描述
        param2: 参数 2 描述

    Returns:
        返回值描述
    """
    # 实现逻辑
    return result
```

然后在 `main.py` 中的 `factorio_agent` 初始化中添加该工具。

### 修改系统提示

修改 `config.toml` 中的 `system_prompt` 以调整代理的行为和目标。

## 故障排除

### 常见问题

1.  **连接错误**: 确保 Factorio 服务器正在运行且 RCON 已启用
2.  **API 错误**: 检查您的 OpenAI API 密钥是否正确
3.  **最大回合数错误**: 增加 `Runner.run()` 中的 `max_turns` 参数，默认为 10

    ```python
    # 在 main.py 中修改
    result = await Runner.run(factorio_agent, message, max_turns=20)  # 增加到 20 或更多
    ```

### 日志示例

查看 `factorio_agent.log` 文件以获取详细的运行时日志和错误信息。

```log
2025-03-20 11:09:20,587 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 200 OK"
2025-03-20 11:09:20,850 - factorio_agent - INFO - Step 7 - Agent response: ### Current Game State
- **Player Position:** (x: -17.5, y: -118.5)
- **Inventory:** 1 wood
- **Nearby Resources:** A large coal deposit surrounding the player

### Analysis
The location features a substantial coal reserve, which can be utilized to fuel basic industries. The inventory is minimal with only one piece of wood, highlighting the need to gather more resources to expand and automate our base operations.

### Next Step Plan
1. **Objective:** Establish a temporary mining setup to begin extracting coal.
2. **Action Plan:**
   - Find available entity prototypes to create a mining drill if materials permit.
   - If the materials allow, place a mining drill on coal and start extraction.

### Actions to Execute
1. Check available prototypes for mining equipment.
2. Decide on extraction setup based on available entities.
```

## 许可证

本项目基于 MIT 许可证发布 - 详情请查看 [LICENSE](LICENSE) 文件。
