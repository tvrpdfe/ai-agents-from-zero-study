"""
LangChain 1.x 官方推荐的 Tool Calling（工具调用）示例

涵盖两种官方推荐用法：
  方式一：model.bind_tools() —— 基础工具调用，手动执行工具并回传结果
  方式二：create_agent()     —— LangChain 1.x 全新的统一 Agent API，
                                自动完成「模型决策 → 调用工具 → 回传结果 → 生成答案」的循环

运行前准备：
  pip install -U langchain langchain-openai
  并设置环境变量 OPENAI_API_KEY
"""

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage


# ---------------------------------------------------------------------------
# 1. 定义工具：使用 @tool 装饰器
#    - docstring 即工具描述（必填，模型靠它决定何时调用）
#    - 参数类型注解会自动生成 JSON Schema
# ---------------------------------------------------------------------------
@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气。"""
    # 示例返回假数据，实际使用时可替换为真实天气 API
    return f"{city}：晴，气温 25°C，微风。"


@tool
def multiply(a: float, b: float) -> float:
    """计算两个数的乘积。"""
    return a * b


TOOLS = [get_weather, multiply]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ---------------------------------------------------------------------------
# 方式一：bind_tools —— 手动控制工具调用流程
# ---------------------------------------------------------------------------
def demo_bind_tools() -> None:
    # init_chat_model 是 1.x 推荐的模型初始化方式，换厂商只需改字符串，
    # 例如 "anthropic:claude-sonnet-4-5"、"google_genai:gemini-2.0-flash"
    model = init_chat_model("openai:gpt-4o-mini", temperature=0)
    model_with_tools = model.bind_tools(TOOLS)

    messages = [HumanMessage(content="北京天气怎么样？另外帮我算一下 12.5 乘以 8。")]

    # 第一次调用：模型不直接回答，而是返回 tool_calls（支持一次请求多个工具）
    ai_msg = model_with_tools.invoke(messages)
    messages.append(ai_msg)

    print("模型请求的工具调用：")
    for tc in ai_msg.tool_calls:
        print(f"  {tc['name']}{tc['args']}")

    # 执行工具：把 tool_call 字典直接传给 tool.invoke()，会自动返回 ToolMessage
    for tc in ai_msg.tool_calls:
        tool_msg = TOOLS_BY_NAME[tc["name"]].invoke(tc)
        messages.append(tool_msg)

    # 第二次调用：模型根据工具结果生成最终自然语言回答
    final = model_with_tools.invoke(messages)
    print("最终回答：", final.content)


# ---------------------------------------------------------------------------
# 方式二：create_agent —— LangChain 1.x 官方推荐的 Agent 构建方式
#   自动循环：LLM 决策 → 执行工具 → 结果回传 → 直到产出最终答案
# ---------------------------------------------------------------------------
def demo_create_agent() -> None:
    agent = create_agent(
        model="openai:gpt-4o-mini",  # 也可以直接传 init_chat_model 得到的模型实例
        tools=TOOLS,
        system_prompt="你是一个简洁有用的中文助手。",
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "上海天气如何？顺便算算 7 乘 6 等于多少。"}]}
    )

    # result["messages"] 是完整对话记录（含工具调用过程），最后一条即最终答案
    print("最终回答：", result["messages"][-1].content)


if __name__ == "__main__":
    print("=" * 20, "方式一：bind_tools", "=" * 20)
    demo_bind_tools()
    print("=" * 20, "方式二：create_agent", "=" * 20)
    demo_create_agent()
