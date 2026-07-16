"""
【案例】顺序链：Prompt → Model → Parser 一条线执行

对应教程章节：第 15 章 - LCEL 与链式调用 → 4.1 RunnableSequence（顺序链）

知识点速览：
- 这是最经典的 LCEL 入门案例：`prompt | model | parser`。
- 这里要区分两个概念：LCEL 是“把多个 Runnable 连起来的写法”，而真正得到的可执行对象是 Chain；这个 Chain 的具体类型通常就是 `RunnableSequence`。
- prompt、model、parser 都实现了 Runnable 接口，所以既可以分步 `invoke()`，也可以先用 `|` 组合后再整体 `invoke()`。
"""

import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

# 创建聊天提示模板（Runnable 子类）：包含系统角色与用户问题占位符
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个{role}，请简短回答我提出的问题"),
        ("human", "请回答:{question}"),
    ]
)

# 使用 invoke 渲染提示词，返回 PromptValue，可直接交给模型（统一接口）
prompt = chat_prompt.invoke(
    {"role": "AI助手", "question": "什么是LangChain，简洁回答100字以内"}
)
logger.info(prompt)

# 初始化聊天模型（同样实现 Runnable，支持 invoke/stream/batch）
model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 模型接收上一步的 PromptValue，返回 AIMessage
result = model.invoke(prompt)
logger.info(f"********>模型原始输出:\n{result}")

# 字符串输出解析器（Runnable）：从 AIMessage 中取出文本，得到更适合业务继续处理的文本结果
parser = StrOutputParser()

# 解析器接收 AIMessage，这里得到的是文本结果
response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info(f"结果类型: {type(response)}")

print()
print("*" * 60)
print()

# 用管道符 | 构建顺序链；LCEL 是写法，组合后的 chain 才是最终得到的 RunnableSequence 对象
chain = chat_prompt | model | parser

# 链整体也是 Runnable：一次 invoke 完成「渲染 → 模型 → 解析」，入参为提示词变量
result_chain = chain.invoke(
    {"role": "AI助手", "question": "什么是LangChain，简洁回答100字以内"}
)
logger.info(f"Chain执行结果:\n{result_chain}")
logger.info(f"Chain执行结果类型: {type(result_chain)}")

print()
print(type(chain))

"""
【输出示例】
2026-03-06 10:09:39.882 | INFO     | __main__:<module>:30 - messages=[SystemMessage(content='你是一个AI助手，请简短回答我提出的问题', additional_kwargs={}, response_metadata={}), HumanMessage(content='请回答:什么是LangChain，简洁回答100字以内', additional_kwargs={}, response_metadata={})]
2026-03-06 10:09:42.059 | INFO     | __main__:<module>:42 - ********>模型原始输出:
content='LangChain 是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具等），支持提示工程、外部数据接入、多步推理与状态管理，简化 LLM 应用的开发与集成。' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 62, 'prompt_tokens': 38, 'total_tokens': 100, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-45f313fd-c388-9498-baa4-c9036e7644a1', 'finish_reason': 'stop', 'logprobs': None} id='lc_run--019cc0e8-5f78-7ef3-a751-d1a4bcfba176-0' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 38, 'output_tokens': 62, 'total_tokens': 100, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}
2026-03-06 10:09:42.059 | INFO     | __main__:<module>:49 - 解析后的结构化结果:
LangChain 是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具等），支持提示工程、外部数据接入、多步推理与状态管理，简化 LLM 应用的开发与集成。
2026-03-06 10:09:42.059 | INFO     | __main__:<module>:50 - 结果类型: <class 'langchain_core.messages.base.TextAccessor'>
# ************************************************************

# 2026-03-06 10:09:44.073 | INFO     | __main__:<module>:61 - Chain执行结果:
# LangChain是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具等），支持提示工程、数据检索增强（RAG）、多步推理和外部工具调用，简化LLM应用的开发与集成。
# 2026-03-06 10:09:44.073 | INFO     | __main__:<module>:62 - Chain执行结果类型: <class 'langchain_core.messages.base.TextAccessor'>

# <class 'langchain_core.runnables.base.RunnableSequence'>

"""
