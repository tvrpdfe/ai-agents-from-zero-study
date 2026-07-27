"""
【案例】ReAct 模式：推理 + 行动的多步工具调用（产品搜索与库存查询）

对应教程章节：第 21 章 - Agent 智能体 → 5、实操与案例（5.2 ReAct）

知识点速览：
- ReAct（Reason + Act）是 Agent 最经典、最适合入门的一种工作机制：先推理，再行动，再根据结果继续推理。
  它不是 Agent 的唯一形态，但最适合帮助初学者看懂“为什么 Agent 不只是一次回答”。
- 本案例提供两个 Tool：search_products（按类别查产品）、check_inventory（查库存）；Agent 自主决定
  调用顺序与次数（如先搜索再查库存），体现「多步、有条件」的决策能力。
- 通过 `result["messages"]` 可追踪完整对话：AIMessage（含 `tool_calls`）、ToolMessage（工具输出）、
  最终 AIMessage（文本回答）。这和新版教程里强调的“消息视角理解 Agent”是对应的。
- 本案例使用 `create_agent + 本地 @tool` 这条 1.x 路线；如果真实项目里想进一步观察执行过程，
  还可以结合 `stream()` 或 LangSmith 追踪，但这个文件先聚焦 ReAct 本身。

关于 @tool 与 MCP：
- 本案例使用 LangChain 的 @tool，在「当前进程」内定义并执行工具，不能直接改成 @mcp.tool() 这种形式。
- MCP 的工具是在「MCP 服务端」定义和运行的：需要在另一侧起 MCP 服务（如 11-mcp 下的 McpServer/McpServerByFastMCP），
  在服务里用 MCP SDK 暴露工具；本进程作为「客户端」通过 mcp.json + MultiServerMCPClient.get_tools() 拿到工具列表再交给 Agent。
- 因此有两种用法二选一：① 本地 @tool，直接传给 create_agent（本案例）；② 用 MCP 服务 + McpClientAgent 的方式
  连接并 get_tools()（见 11-mcp/McpClientAgent.py）。不能在同一文件里把 @tool 简单替换成 @mcp.tool()。
"""

import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

# 模拟产品数据库：类别 -> 产品列表（id、name、popularity、price）
PRODUCT_DATABASE = {
    "无线耳机": [
        {"id": "WH-1000XM5", "name": "索尼 WH-1000XM5", "popularity": 95, "price": 299},
        {"id": "QC45", "name": "Bose QuietComfort 45", "popularity": 88, "price": 329},
        {"id": "AIRMAX", "name": "苹果 AirPods Max", "popularity": 92, "price": 549},
        {"id": "PXC550", "name": "森海塞尔 PXC 550", "popularity": 76, "price": 299},
        {"id": "HT450", "name": "JBL Tune 760NC", "popularity": 82, "price": 99},
    ],
    "游戏鼠标": [
        {"id": "GPW", "name": "罗技 G Pro 无线", "popularity": 90, "price": 129},
        {"id": "VIPER", "name": "雷蛇 Viper V2 Pro", "popularity": 87, "price": 149},
        {"id": "DAV3", "name": "雷蛇 DeathAdder V3", "popularity": 85, "price": 119},
    ],
    "笔记本电脑": [
        {"id": "MBP14", "name": "MacBook Pro 14英寸", "popularity": 94, "price": 1999},
        {"id": "XPS13", "name": "戴尔 XPS 13", "popularity": 89, "price": 1299},
        {"id": "TPX1", "name": "ThinkPad X1 Carbon", "popularity": 86, "price": 1499},
    ],
}

# 模拟库存：产品 ID -> 库存数量与仓位
INVENTORY_DATABASE = {
    "WH-1000XM5": {"stock": 10, "location": "仓库-A"},
    "QC45": {"stock": 0, "location": "仓库-B"},
    "AIRMAX": {"stock": 5, "location": "仓库-C"},
    "PXC550": {"stock": 15, "location": "仓库-A"},
    "HT450": {"stock": 25, "location": "仓库-B"},
    "GPW": {"stock": 8, "location": "仓库-C"},
    "VIPER": {"stock": 12, "location": "仓库-A"},
    "DAV3": {"stock": 3, "location": "仓库-B"},
    "MBP14": {"stock": 7, "location": "仓库-C"},
    "XPS13": {"stock": 0, "location": "仓库-A"},
    "TPX1": {"stock": 4, "location": "仓库-B"},
}


@tool
def search_products(query: str) -> str:
    """搜索产品并返回按受欢迎度排序的结果（Tool：能力封装，供 Agent 调用）"""
    print(f"🔍 [工具调用] search_products('{query}')")

    keyword_mapping = {
        "无线耳机": ["无线耳机", "蓝牙耳机", "头戴式耳机", "耳机"],
        "游戏鼠标": ["游戏鼠标", "电竞鼠标", "鼠标"],
        "笔记本电脑": ["笔记本电脑", "笔记本", "手提电脑", "电脑"],
    }

    matched_category = None
    for category, keywords in keyword_mapping.items():
        if any(keyword in query for keyword in keywords):
            matched_category = category
            break

    if matched_category and matched_category in PRODUCT_DATABASE:
        products = PRODUCT_DATABASE[matched_category]
        sorted_products = sorted(products, key=lambda x: x["popularity"], reverse=True)
        result = f"找到 {len(sorted_products)} 个匹配 '{query}' 的产品:\n"
        for i, product in enumerate(sorted_products, 1):
            result += f"{i}. {product['name']} (ID: {product['id']}) - 受欢迎度: {product['popularity']}% - ￥{product['price']}\n"
        return result
    return "未找到匹配产品"


@tool
def check_inventory(product_id: str) -> str:
    """检查特定产品的库存状态（Tool：能力封装）"""
    print(f"📦 [工具调用] check_inventory('{product_id}')")

    if product_id in INVENTORY_DATABASE:
        stock_info = INVENTORY_DATABASE[product_id]
        status = "有库存" if stock_info["stock"] > 0 else "缺货"
        return f"产品 {product_id}: {status} ({stock_info['stock']} 件库存) - 位置: {stock_info['location']}"
    return f"未找到产品ID: {product_id}"


model = ChatOpenAI(
    model="grok-4.5",
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://www.micuapi.ai/v1",
)

# 系统提示中明确 ReAct：先推理、再选工具、基于结果继续推理直至得到完整答案
# 这里是在“用 ReAct 作为最常见入门机制”，并不代表 Agent 只有这一种工作方式
agent = create_agent(
    model,
    tools=[search_products, check_inventory],
    system_prompt="""你是电商助手，遵循ReAct模式：
    1. 先推理用户需求
    2. 选择合适的工具执行操作
    3. 基于工具结果进行下一步推理
    4. 重复直到获得完整答案

    保持推理步骤简洁明了。""",
)

# 测试：一次问题可能触发多轮「推理 → 选工具 → 观察 → 再推理」
result1 = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "查找当前最受欢迎的无线耳机并检查是否有库存"}
        ]
    }
)

print("\n" + "=" * 40)
print("📊 最终结果:")
for msg in result1["messages"]:
    if hasattr(msg, "content"):
        print(f"{msg.__class__.__name__}: {msg.content}")
print("=" * 40)


# 可选：逐条解析 messages，观察 ReAct 循环（AIMessage.tool_calls、ToolMessage、最终 AIMessage）
# 这也是理解现代 Tool Calling Agent 的一个非常直观的办法
def track_react_cycle(messages):
    print("ReAct循环步骤分析:")
    step = 1
    for i, msg in enumerate(messages):
        msg_type = msg.__class__.__name__
        if msg_type == "AIMessage" and hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"\n🔄 步骤{step}: Reasoning + Acting")
            for tool_call in msg.tool_calls:
                print(f"   🛠️  工具调用: {tool_call['name']}({tool_call['args']})")
            step += 1
        elif msg_type == "ToolMessage":
            print(f"   📋  观察结果: {msg.content[:80]}...")
        elif msg_type == "AIMessage" and not (
            hasattr(msg, "tool_calls") and msg.tool_calls
        ):
            print(f"\n✅ 最终回答: {msg.content}")


track_react_cycle(result1["messages"])

"""
【输出案例】
🔍 [工具调用] search_products('无线耳机')
📦 [工具调用] check_inventory('WH-1000XM5')
"""

# ========================================
# 📊 最终结果:
# HumanMessage: 查找当前最受欢迎的无线耳机并检查是否有库存
# AIMessage: 1. 首先，我需要搜索当前最受欢迎的无线耳机。
# 2. 然后，从搜索结果中获取最受欢迎的产品ID，并检查其库存状态。


# ToolMessage: 找到 5 个匹配 '无线耳机' 的产品:
# 1. 索尼 WH-1000XM5 (ID: WH-1000XM5) - 受欢迎度: 95% - ￥299
# 2. 苹果 AirPods Max (ID: AIRMAX) - 受欢迎度: 92% - ￥549
# 3. Bose QuietComfort 45 (ID: QC45) - 受欢迎度: 88% - ￥329
# 4. JBL Tune 760NC (ID: HT450) - 受欢迎度: 82% - ￥99
# 5. 森海塞尔 PXC 550 (ID: PXC550) - 受欢迎度: 76% - ￥299

# AIMessage: 1. 根据搜索结果，最受欢迎的无线耳机是索尼 WH-1000XM5（ID: WH-1000XM5），受欢迎度为95%。
# 2. 接下来，我将检查该产品的库存状态。


# ToolMessage: 产品 WH-1000XM5: 有库存 (10 件库存) - 位置: 仓库-A
# AIMessage: 索尼 WH-1000XM5 是当前最受欢迎的无线耳机，受欢迎度为95%，且有库存（10件），存放于仓库-A。
# ========================================
# ReAct循环步骤分析:

# 🔄 步骤1: Reasoning + Acting
#    🛠️  工具调用: search_products({'query': '无线耳机'})
#    📋  观察结果: 找到 5 个匹配 '无线耳机' 的产品:
# 1. 索尼 WH-1000XM5 (ID: WH-1000XM5) - 受欢迎度: 95% - ￥299
# 2. 苹果 ...

# 🔄 步骤2: Reasoning + Acting
#    🛠️  工具调用: check_inventory({'product_id': 'WH-1000XM5'})
#    📋  观察结果: 产品 WH-1000XM5: 有库存 (10 件库存) - 位置: 仓库-A...

# ✅ 最终回答: 索尼 WH-1000XM5 是当前最受欢迎的无线耳机，受欢迎度为95%，且有库存（10件），存放于仓库-A。
