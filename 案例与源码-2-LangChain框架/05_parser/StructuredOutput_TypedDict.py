"""
【案例】用 TypedDict + Annotated 做结构化输出

对应教程章节：第 14 章 - 输出解析器 → 3、结构化输出（TypedDict / Pydantic / Annotated）

知识点速览：
一、什么是「结构化输出」？
  - 希望模型返回的不是随便一段话，而是固定结构的数据（如指定字段的 dict），方便程序后续处理。
  - LangChain 支持用 TypedDict（Python 标准库）或 Pydantic 定义结构，再由模型按该结构生成并解析。

二、with_structured_output 做什么？
  - 在模型上调用 llm.with_structured_output(某个类型)，会返回一个「带了结构化输出能力」的可调用对象。
  - 调用 .invoke(messages) 时，模型会被引导输出符合该结构的 JSON，并自动解析成 Python 的 dict（或对应类型），无需再手写 Parser。

三、本案例：用 typing.TypedDict 定义 Animal（动物名 + emoji）、AnimalList（动物列表）；用 Annotated 给字段加描述，便于模型理解各字段含义；最后用 llm.with_structured_output(AnimalList) 一次得到结构化结果。
"""

import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv(encoding="utf-8")

llm = init_chat_model(
    model="grok-4.5",
    model_provider="openai",  # OpenAI 兼容接口
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://www.micuapi.ai/v1",
)


# 用 TypedDict 定义「一个动物」的结构；Annotated 里的字符串是给模型看的描述，便于生成合适内容
class Animal(TypedDict):
    animal: Annotated[str, "动物"]
    emoji: Annotated[str, "表情"]


# 定义「动物列表」：一个字段 animals，类型是 Animal 的列表
class AnimalList(TypedDict):
    animals: Annotated[list[Animal], "动物与表情列表"]


# 普通对话消息
messages = [{"role": "user", "content": "任意生成三种动物，以及他们的 emoji 表情"}]

# 给模型绑定「结构化输出」：按 AnimalList 的结构返回并解析
llm_with_structured_output = llm.with_structured_output(AnimalList)
resp = llm_with_structured_output.invoke(messages)
print(
    resp
)  # 得到符合 AnimalList 的 dict，如 {"animals": [{"animal": "猫", "emoji": "🐱"}, ...]}

"""
【输出示例】
{'animals': [{'animal': '狗', 'emoji': '🐶'}, {'animal': '猫', 'emoji': '🐱'}, {'animal': '鸟', 'emoji': '🐦'}]}
"""
