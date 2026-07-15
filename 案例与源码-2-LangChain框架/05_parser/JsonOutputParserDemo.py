"""
【案例】JsonOutputParser 基础用法：在提示词里直接要求返回 JSON

对应教程章节：第 14 章 - 输出解析器 → 2、常用输出解析器用法

知识点速览：
一、JsonOutputParser 是什么？
  - 把模型的自由文本输出解析成结构化 JSON（Python 里就是 dict / list）。
  - 模型若返回的是「像 JSON 的文本」，解析器会尝试解析，得到字典后便于后续逻辑、入库或展示。

二、本案例做法：在 system 提示词里手写要求，例如「结果返回 json 格式，q 字段表示问题，a 字段表示答案」。
  - 不依赖 get_format_instructions()，适合结构简单、自己说清楚就够用的场景。
  - 进阶做法见 JsonOutputParser_GetFormatInstructions.py：用 get_format_instructions() 生成格式说明再拼进提示词。
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger

load_dotenv(encoding="utf-8")

# 在系统消息里直接写明：返回 json，且包含 q（问题）、a（答案）字段
chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个{role}，请简短回答我提出的问题，结果返回json格式，q字段表示问题，a字段表示答案。",
        ),
        ("human", "请回答:{question}"),
    ]
)

prompt = chat_prompt.invoke(
    {"role": "AI助手", "question": "什么是LangChain，简洁回答100字以内"}
)
logger.info(prompt)

model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 模型返回的可能是带 JSON 的文本
result = model.invoke(prompt)
logger.info(f"模型原始输出:\n{result}")

print("*" * 60)

# 创建 JSON 解析器（不绑 Pydantic 时，解析结果为 dict/list）
parser = JsonOutputParser()
# 尝试从 result 的 content 中解析出 JSON
response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info("\n")
logger.info(f"结果类型: {type(response)}")  # <class 'dict'>


"""
【输出示例】
2026-02-26 12:00:54.190 | INFO     | __main__:<module>:29 - messages=[SystemMessage(content='你是一个AI助手，请简短回答我提出的问题，结果返回json格式，q字段表示问题，a字段表示答案。', additional_kwargs={}, response_metadata={}), HumanMessage(content='请回答:什么是LangChain，简洁回答100字以内', additional_kwargs={}, response_metadata={})]
2026-02-26 12:00:56.500 | INFO     | __main__:<module>:40 - 模型原始输出:
content='{"q": "什么是LangChain，简洁回答100字以内", "a": "LangChain是一个开源框架，用于构建基于大语言模型（LLM）的应用程序，支持链式调用、数据连接、记忆管理与工具集成，简化提示工程、RAG和Agent开发。"}' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 65, 'prompt_tokens': 54, 'total_tokens': 119, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-f940cf51-c792-904e-9ed9-d2808c5ab264', 'finish_reason': 'stop', 'logprobs': None} id='lc_run--019c981b-56ff-73b0-92fd-48ed999ee369-0' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 54, 'output_tokens': 65, 'total_tokens': 119, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}
************************************************************
2026-02-26 12:00:56.501 | INFO     | __main__:<module>:48 - 解析后的结构化结果:
{'q': '什么是LangChain，简洁回答100字以内', 'a': 'LangChain是一个开源框架，用于构建基于大语言模型（LLM）的应用程序，支持链式调用、数据连接、记忆管理与工具集成，简化提示工程、RAG和Agent开发。'}
2026-02-26 12:00:56.501 | INFO     | __main__:<module>:49 -
"""

# 2026-02-26 12:00:56.501 | INFO     | __main__:<module>:50 - 结果类型: <class 'dict'>
