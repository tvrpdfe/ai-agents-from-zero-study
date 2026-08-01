"""
【案例】多节点、固定边的完整图：input → process → output 三个节点，状态字段 process_data 在节点间传递，并在默认覆盖规则下被后续节点更新。

对应教程章节：第 23 章 - LangGraph API：图与状态 → 1、Graph API 之 Graph（图）

知识点速览：
- StateGraph(GraphState) 指定状态类型后，各节点接收完整 state，返回对 state 的「部分更新」字典。
- 本例的重点是“图怎么搭起来”，不是“状态怎么累积起来”；未为字段指定 Reducer 时，默认覆盖：后一节点返回的 process_data 会覆盖前一节点的值。
- 固定边：add_edge 依次串联 START → input → process → output → END，执行顺序确定。
- 编译后 invoke(initial_state) 传入初始 process_data，结果中最终保留的是最后一次写入该字段的内容。
"""

from typing import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph
import os
import uuid

"""图的构建流程：
1、初始化一个StateGraph实例。
2、添加节点。
3、定义边，将所有的节点连接起来。
4、设置特殊节点，入口和出口（可选）。
5、编译图。
6、执行工作流。"""


# 定义状态：process_data 用于在节点间传递；本例未指定 Reducer，因此后续节点会按默认覆盖规则更新它
class GraphState(TypedDict):
    process_data: dict


def input_node(state: GraphState) -> dict:
    """入口节点：写入初始 process_data。"""
    print(f"input_node 节点执行 state.get('process_data'): {state.get('process_data')}")
    return {"process_data": {"input": "input_value"}}


def process_node(state: GraphState) -> dict:
    """处理节点：更新 process_data。"""
    print(
        f"process_node 节点执行 state.get('process_data'): {state.get('process_data')}"
    )
    return {"process_data": {"process": "process_value9527"}}


def output_node(state: GraphState) -> dict:
    """出口节点：读取并返回当前 process_data。"""
    print(
        f"output_node 节点执行 state.get('process_data'): {state.get('process_data')}"
    )
    return {"process_data": state.get("process_data")}


# 创建状态图并指定状态类型
graph = StateGraph(GraphState)
graph.add_node("input", input_node)
graph.add_node("process", process_node)
graph.add_node("output", output_node)

# 固定边：start → input → process → output → end
graph.add_edge(START, "input")
graph.add_edge("input", "process")
graph.add_edge("process", "output")
graph.add_edge("output", END)

# 编译后执行；传入的初始 state 会与各节点返回值按 Reducer 规则合并
app = graph.compile()
result = app.invoke({"process_data": {"name": "测试数据", "value": 123456}})
print(f"最后的结果是:{result}")

# 可视化
print(app.get_graph().print_ascii())
print("=================================")
print(app.get_graph().draw_mermaid())
# 可选：生成 PNG 图片（依赖 mermaid.ink 或 Pyppeteer，易受网络影响）
png_bytes = app.get_graph().draw_mermaid_png(max_retries=2, retry_delay=2.0)
output_path = os.path.join(
    os.path.dirname(__file__), "langgraph" + str(uuid.uuid4())[:8] + ".png"
)
with open(output_path, "wb") as f:
    f.write(png_bytes)
print(f"图片已生成：{output_path}")

"""
【输出示例】
input_node 节点执行 state.get('process_data'): {'name': '测试数据', 'value': 123456}
process_node 节点执行 state.get('process_data'): {'input': 'input_value'}
output_node 节点执行 state.get('process_data'): {'process': 'process_value9527'}
最后的结果是:{'process_data': {'process': 'process_value9527'}}
+-----------+
| __start__ |
+-----------+
      *
      *
      *
  +-------+
  | input |
  +-------+
      *
      *
      *
 +---------+
 | process |
 +---------+
      *
      *
      *
  +--------+
  | output |
  +--------+
      *
      *
      *
 +---------+
 | __end__ |
 +---------+
None
=================================
---
config:
  flowchart:
    curve: linear
---
graph TD;
        __start__([<p>__start__</p>]):::first
        input(input)
        process(process)
        output(output)
        __end__([<p>__end__</p>]):::last
        __start__ --> input;
        input --> process;
        process --> output;
        output --> __end__;
        classDef default fill:#f2f0ff,line-height:1.2
        classDef first fill-opacity:0
        classDef last fill:#bfb6fc
"""
