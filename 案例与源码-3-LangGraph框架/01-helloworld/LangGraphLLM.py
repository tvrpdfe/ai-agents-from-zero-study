"""
【案例】接入大模型的最小对话图：用户消息 → model 节点 → 模型回复写回 messages，演示 LangGraph 如何和 LangChain 模型调用衔接，以及为什么对话状态通常要配 add_messages

对应教程章节：第 22 章 - LangGraph 概述与快速入门 → 2、HelloWorld 快速入门

知识点速览：
- add_messages：LangGraph 内置 Reducer，专门适合消息列表字段；它的语义是“把新消息追加进历史消息”，而不是把 messages 整个覆盖掉。
- messages 字段写成 Annotated[List, add_messages] 后，节点只需要 return {"messages": [reply]} 这种增量更新，历史对话不会丢失。
- model_node(state) 直接把 state["messages"] 交给 llm.invoke(...)，说明“节点可以只是普通函数，函数内部再调用 LangChain 模型”。
- 图结构是最小单节点对话流 START → model → END；invoke 时传入初始 messages，执行后从 result["messages"][-1].content 读取最新模型回复。
- 模型初始化沿用第 10 章“调用三件套”思维：模型名、API Key、Base URL。本文件保留 api_key=os.getenv("aliQwen-api") 写法不改动。
- 这个案例只是“单节点 LLM 图”的最小雏形；第 23 章会继续解释 add_messages 背后的 Reducer 机制，第 24 章会继续扩展多节点和条件边。
"""

import json
import os
import uuid
from typing import Annotated, List, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, message_to_dict
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")


# 1. 定义状态 State：messages 使用 add_messages 规约器，节点返回的每条新消息会自动追加到列表
class DiliState(TypedDict):
    # add_messages 是 LangGraph 提供的「规约器」（Reducer），来自 langgraph.graph.message。
    # 含义：该字段不是「覆盖」更新，而是「追加」——节点只返回新增的消息（如 [reply]），
    # 框架会把它们合并到当前消息列表末尾，适合多轮对话、多节点共同往同一列表写消息。
    # 若不用 add_messages，节点返回 {"messages": [reply]} 会直接覆盖掉之前的对话历史。
    messages: Annotated[List, add_messages]


# 2. 初始化大模型（与第 10 章调用方式一致）
llm = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# 3. 定义节点 Nodes：将当前消息列表交给模型，返回新消息字典（add_messages 会追加到 state）
def model_node(state: DiliState):
    reply = llm.invoke(state["messages"])
    return {"messages": [reply]}


# 4. 构建图：单节点 model，START → model → END
graph = StateGraph(DiliState)
graph.add_node("model", model_node)
graph.add_edge(START, "model")
graph.add_edge("model", END)

# 5. 编译并执行
app = graph.compile()
# 传入初始消息（HumanMessage 或字符串均可，视模型封装而定）
result = app.invoke(
    {"messages": [HumanMessage(content="请用一句话解释什么是 LangGraph。")]}
)
# 或: result = app.invoke({"messages": "请用一句话解释什么是 LangGraph。"})

print("模型回答：", result["messages"][-1].content)

# 直接格式化输出 result：default 把消息对象转成 dict，其它不可序列化用 str 兜底
print("\n--- result 格式化输出 ---")
print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        default=lambda o: message_to_dict(o) if isinstance(o, BaseMessage) else str(o),
    )
)

# 可视化
print(app.get_graph().print_ascii())
print("=" * 50)
# print(app.get_graph().draw_mermaid())
# print("=" * 50)

png_bytes = app.get_graph().draw_mermaid_png()
output_path = os.path.join(
    os.path.dirname(__file__), "langgraph" + str(uuid.uuid4())[:8] + ".png"
)
with open(output_path, "wb") as f:
    f.write(png_bytes)
print(f"图片已生成：{output_path}")


"""
【输出示例】
模型回答： LangGraph 是一个基于图（Graph）的框架，用于构建具有状态、记忆和循环逻辑的复杂 AI 代理（Agent）工作流，它扩展自 LangChain，通过节点（Nodes）和边（Edges）定义可暂停、恢复、带状态的有向图执行流程，特别适合实现多步骤推理、工具调用、人工干预和长期对话等动态场景。


--- result 格式化输出 ---
{
  "messages": [
    {
      "type": "human",
      "data": {
        "content": "请用一句话解释什么是 LangGraph。",
        "additional_kwargs": {},
        "response_metadata": {},
        "type": "human",
        "name": null,
        "id": "be0768a0-4831-4fdc-a86f-dfe73b8a42de"
      }
    },
    {
      "type": "ai",
      "data": {
        "content": "LangGraph 是一个基于图（Graph）的框架，用于构建具有状态、记忆和循环逻辑的复杂 AI 代理（Agent）工作流，它扩展自 LangChain，通过节点（Nodes）和边（Edges）定义可暂停、恢复、带状态的有向图执行流程，特别适合实现多步骤推理、工具调用、人工干预和长期对话等动态场景。",
        "additional_kwargs": {
          "refusal": null
        },
        "response_metadata": {
          "token_usage": {
            "completion_tokens": 83,
            "prompt_tokens": 16,
            "total_tokens": 99,
            "completion_tokens_details": null,
            "prompt_tokens_details": {
              "audio_tokens": null,
              "cached_tokens": 0
            }
          },
          "model_provider": "openai",
          "model_name": "qwen-plus",
          "system_fingerprint": null,
          "id": "chatcmpl-e336cb84-dd3e-9665-90db-5a9a570d4be0",
          "finish_reason": "stop",
          "logprobs": null
        },
        "type": "ai",
        "name": null,
        "id": "lc_run--019cf0a4-cf09-7bd3-90d3-3e383a7aff0a-0",
        "tool_calls": [],
        "invalid_tool_calls": [],
        "usage_metadata": {
          "input_tokens": 16,
          "output_tokens": 83,
          "total_tokens": 99,
          "input_token_details": {
            "cache_read": 0
          },
          "output_token_details": {}
        }
      }
    }
  ]
}
+-----------+
| __start__ |
+-----------+
      *
      *
      *
  +-------+
  | model |
  +-------+
      *
      *
      *
 +---------+
 | __end__ |
 +---------+
None
==================================================
---
config:
  flowchart:
    curve: linear
---
graph TD;
        __start__([<p>__start__</p>]):::first
        model(model)
        __end__([<p>__end__</p>]):::last
        __start__ --> model;
        model --> __end__;
        classDef default fill:#f2f0ff,line-height:1.2
        classDef first fill-opacity:0
        classDef last fill:#bfb6fc

==================================================
"""
