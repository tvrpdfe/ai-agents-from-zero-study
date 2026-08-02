"""
【案例】多种 Reducer 并存：同一 State 里 `messages` 用 add_messages 追加、`tags` 用 operator.add 拼接列表、`score` 用 operator.add 做数值累加；演示同一份 State 里不同字段可以有不同合并规则。

对应教程章节：第 23 章 - LangGraph API：图与状态 → 3、State 的更新机制：Reducer（规约函数）

知识点速览：
- 这是第 23 章里最适合建立“State = Schema + Reducer”整体直觉的案例：字段定义是一层，字段怎么合并是另一层。
- add_messages：节点只返回「增量」消息，自动与历史合并为一条对话链；invoke 里也可传 OpenAI 风格的 `{\"role\", \"content\"}` 字典，运行时会转为 Message 对象。
- operator.add 作用于列表时相当于拼接，作用于 float 时为普通加法累加；同一个 State 里完全可以给不同字段配置不同 Reducer。
- 从同一 START 连到多个节点时，本例重点是观察“不同字段如何被各自的 Reducer 合并”，而不是把并行分支的执行先后当成业务契约。
"""

from typing import Annotated, List

import operator
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ChatState(TypedDict):
    # 消息历史：add_messages 规约，新消息追加而非整表覆盖（与 StateReducer_AddMessages 一致可用 List）
    messages: Annotated[List, add_messages]
    # 标签列表：operator.add 将各节点返回的列表拼到已有列表后
    tags: Annotated[List[str], operator.add]
    # 累计分数：operator.add 做浮点数相加
    score: Annotated[float, operator.add]


def process_user_message(state: ChatState) -> dict:
    # 获取最新消息；修复/注意：须用 .content 读正文（dict 入参在运行时已转为 HumanMessage 等对象，勿当普通 str 用）
    user_message = state["messages"][-1]
    return {
        # add_messages 会把本条 assistant 回复与历史合并
        "messages": [("assistant", f"Echo: {user_message.content}")],
        "tags": ["processed"],
        "score": 1.0,
    }


def add_sentiment_tag(state: ChatState) -> dict:
    # 本节点不写 messages，则 messages 仅由其他节点更新；tags/score 仍参与 operator.add 合并
    return {"tags": ["positive"], "score": 0.5}


def run_demo():
    builder = StateGraph(ChatState)
    builder.add_node("process", process_user_message)
    builder.add_node("sentiment", add_sentiment_tag)

    # 两节点都从 START 接入：并行分支，各自跑到 END
    builder.add_edge(START, "process")
    builder.add_edge("process", "sentiment")
    builder.add_edge("sentiment", END)

    graph = builder.compile()

    # invoke 只接收一个状态字典；messages 可用 dict 列表，与 Chat API 习惯一致
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "tags": ["greeting"],
            "score": 0.0,
        }
    )
    print(result)


if __name__ == "__main__":
    run_demo()

"""
【输出示例】
{'messages': [HumanMessage(content='Hello, how are you?', additional_kwargs={}, response_metadata={}, id='4350252b-ace7-429a-8cc8-67d232d91f42'), AIMessage(content='Echo: Hello, how are you?', additional_kwargs={}, response_metadata={}, id='ab394788-89d0-45f2-a6b0-5252a448ebb1', tool_calls=[], invalid_tool_calls=[])], 'tags': ['greeting', 'processed', 'positive'], 'score': 1.5}
"""
