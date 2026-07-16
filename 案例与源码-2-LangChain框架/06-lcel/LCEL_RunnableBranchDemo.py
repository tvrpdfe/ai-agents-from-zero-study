"""
【案例】分支链：根据输入条件选择不同子链执行

对应教程章节：第 15 章 - LCEL 与链式调用 → 4.2 RunnableBranch（分支链）

知识点速览：
- `RunnableBranch` 解决的是“同一个输入，不一定走同一条链”的问题，本质上是 LCEL 里的路由层。
- 传入若干 `(条件, Runnable)` 对和一个默认分支后，执行时会按顺序判断条件，命中的第一条分支会被执行；最后一个未成对的 Runnable 通常就是默认分支。
- 每个分支内部仍然可以是 `prompt | model | parser` 这样的顺序链，所以分支链可以理解为“外层路由 + 内层子链”。
"""

import os

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch
from loguru import logger


from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

# 英语分支：提示词模板 + 占位符 query
english_prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个英语翻译专家，你叫小英"), ("human", "{query}")]
)

japanese_prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个日语翻译专家，你叫小日"), ("human", "{query}")]
)

korean_prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个韩语翻译专家，你叫小韩"), ("human", "{query}")]
)


def determine_language(inputs):
    """根据 query 中的关键词判断语言类型，供分支条件使用。"""
    query = inputs["query"]
    if "日语" in query:
        return "japanese"
    elif "韩语" in query:
        return "korean"
    else:
        return "english"


model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

parser = StrOutputParser()

# RunnableBranch( (条件1, 子链1), (条件2, 子链2), ..., 默认子链 )
# 条件为可调用对象，接收输入 dict，返回 bool；第一个命中的分支会执行，最后一个参数是默认分支
chain = RunnableBranch(
    (lambda x: determine_language(x) == "japanese", japanese_prompt | model | parser),
    (lambda x: determine_language(x) == "korean", korean_prompt | model | parser),
    (english_prompt | model | parser),  # 默认分支：英语
)

test_queries = [
    {"query": '请你用韩语翻译这句话:"见到你很高兴"'},
    {"query": '请你用日语翻译这句话:"见到你很高兴"'},
    {"query": '请你用英语翻译这句话:"见到你很高兴"'},
]

for query_input in test_queries:
    lang = determine_language(query_input)
    logger.info(f"检测到语言类型: {lang}")

    if lang == "japanese":
        chatPromptTemplate = japanese_prompt
    elif lang == "korean":
        chatPromptTemplate = korean_prompt
    else:
        chatPromptTemplate = english_prompt

    # 仅作演示：格式化后的提示词内容（实际执行时由 chain.invoke 内部完成）
    formatted_messages = chatPromptTemplate.format_messages(**query_input)
    logger.info("格式化后的提示词:")
    for msg in formatted_messages:
        logger.info(f"[{msg.type}]: {msg.content}")

    # 一次 invoke：Branch 会根据 query 自动选分支并执行对应子链
    result = chain.invoke(query_input)
    logger.info(f"输出结果: {result}\n")

"""
【输出示例】
2026-03-06 10:15:54.493 | INFO     | __main__:<module>:77 - 检测到语言类型: korean
2026-03-06 10:15:54.493 | INFO     | __main__:<module>:88 - 格式化后的提示词:
2026-03-06 10:15:54.493 | INFO     | __main__:<module>:90 - [system]: 你是一个韩语翻译专家，你叫小韩
2026-03-06 10:15:54.493 | INFO     | __main__:<module>:90 - [human]: 请你用韩语翻译这句话:"见到你很高兴"
2026-03-06 10:15:55.733 | INFO     | __main__:<module>:94 - 输出结果: 만나서 반갑습니다.

# 2026-03-06 10:15:55.733 | INFO     | __main__:<module>:77 - 检测到语言类型: japanese
# 2026-03-06 10:15:55.733 | INFO     | __main__:<module>:88 - 格式化后的提示词:
# 2026-03-06 10:15:55.733 | INFO     | __main__:<module>:90 - [system]: 你是一个日语翻译专家，你叫小日
# 2026-03-06 10:15:55.733 | INFO     | __main__:<module>:90 - [human]: 请你用日语翻译这句话:"见到你很高兴"
# 2026-03-06 10:15:56.552 | INFO     | __main__:<module>:94 - 输出结果: お会いできて嬉しいです。

# 2026-03-06 10:15:56.552 | INFO     | __main__:<module>:77 - 检测到语言类型: english
# 2026-03-06 10:15:56.552 | INFO     | __main__:<module>:88 - 格式化后的提示词:
# 2026-03-06 10:15:56.552 | INFO     | __main__:<module>:90 - [system]: 你是一个英语翻译专家，你叫小英
# 2026-03-06 10:15:56.552 | INFO     | __main__:<module>:90 - [human]: 请你用英语翻译这句话:"见到你很高兴"
# 2026-03-06 10:15:57.031 | INFO     | __main__:<module>:94 - 输出结果: Nice to meet you.

"""
