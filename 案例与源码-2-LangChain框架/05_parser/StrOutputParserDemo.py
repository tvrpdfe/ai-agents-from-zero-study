"""
【案例】StrOutputParser 字符串解析器

对应教程章节：第 14 章 - 输出解析器 → 2、常用输出解析器用法

知识点速览：
一、为什么需要「输出解析器」？
  - 大模型返回的通常是 AIMessage 等对象，直接拿到的可能是整块对象，不方便当字符串用。
  - 输出解析器的作用：把「模型输出」转成程序里好用的形式（如 str、dict、强类型对象）。

二、StrOutputParser 是什么？
  - LangChain 里最简单的解析器：从模型返回中取出 content 字段，转成 纯字符串，不做 JSON 等结构解析。
  - 适合：只关心「模型说了什么话」、不需要拆成字段的场景。

三、典型流程：构造 Prompt → model.invoke(prompt) 得到 result → parser.invoke(result) 得到 str。
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger

load_dotenv(encoding="utf-8")

# 构造对话模板（与第 13 章 ChatPromptTemplate 用法一致）
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个{role}，请简短回答我提出的问题"),
        ("human", "请回答:{question}"),
    ]
)

# 填充占位符，得到消息列表，供模型使用
prompt = chat_prompt.invoke(
    {"role": "AI助手", "question": "什么是LangChain，简洁回答100字以内"}
)
logger.info(prompt)

# 初始化大模型（需配置 API Key 等）
model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 调用模型：传入 prompt，得到的是 AIMessage 等对象（原始输出）
result = model.invoke(prompt)
logger.info(f"模型原始输出:\n{result}")

# 创建字符串解析器：只做「从 result 里取 content 转成 str」
# 单条 AIMessage 时确实等价于 result.content；用解析器的好处：可链式组合（prompt | model | parser）、
# 流式时统一处理 chunk、多条消息时按约定取最后一条等，且与 JsonOutputParser 等接口一致便于替换。
parser = StrOutputParser()

# 解析：parser.invoke(result) 等价于从 result 中取 content，得到纯字符串
response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info("\n")
logger.info(
    f"结果类型: {type(response)}"
)  # 输出示例: <class 'langchain_core.messages.base.TextAccessor'>

"""
【输出示例】
2026-02-27 14:32:50.639 | INFO     | __main__:<module>:37 - messages=[SystemMessage(content='你是一个AI助手，请简短回答我提出的问题', additional_kwargs={}, response_metadata={}), HumanMessage(content='请回答:什么是LangChain，简洁回答100字以内', additional_kwargs={}, response_metadata={})]
2026-02-27 14:32:54.776 | INFO     | __main__:<module>:49 - 模型原始输出:
content='LangChain 是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具等），支持提示工程、数据检索增强（RAG）、多步推理和外部工具调用，简化 LLM 应用的开发与集成。' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 67, 'prompt_tokens': 38, 'total_tokens': 105, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-7f8b2cc0-7b6a-98c7-8180-4d8fe4433fd3', 'finish_reason': 'stop', 'logprobs': None} id='lc_run--019c9dcc-cdc5-71d3-9b0e-8ca64d9ae28d-0' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 38, 'output_tokens': 67, 'total_tokens': 105, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}
2026-02-27 14:32:54.777 | INFO     | __main__:<module>:56 - 解析后的结构化结果:
LangChain 是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具等），支持提示工程、数据检索增强（RAG）、多步推理和外部工具调用，简化 LLM 应用的开发与集成。
2026-02-27 14:32:54.777 | INFO     | __main__:<module>:57 -
"""
