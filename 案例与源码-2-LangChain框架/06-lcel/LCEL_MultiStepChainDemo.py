"""
【案例】串行链：多步串联，前一步输出作为后一步输入

对应教程章节：第 15 章 - LCEL 与链式调用 → 4.3 多步串行链（Multi-Step Chain）

知识点速览：
- 这个案例真正要学的是“多步串行链”：前一步不是最终答案，而是后一步的原材料。
- 当多条子链首尾相接时，前一步输出会直接流向后一步；如果前后输入输出结构不匹配，就需要插入一次映射。
- 这里用 `lambda` 把第一条子链输出的文本包装成 `{"input": 文本}`，本质上是在做“节点之间的数据适配”。
"""

import os

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 子链 1：用中文介绍某主题，输出为 str
prompt1 = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个知识渊博的计算机专家，请用中文简短回答"),
        ("human", "请简短介绍什么是{topic}"),
    ]
)
parser1 = StrOutputParser()
chain1 = prompt1 | model | parser1

result1 = chain1.invoke({"topic": "langchain"})
logger.info(result1)

# 子链 2：将用户输入翻译成英文，期望入参为 {"input": 文本}
prompt2 = ChatPromptTemplate.from_messages(
    [("system", "你是一个翻译助手，将用户输入内容翻译成英文"), ("human", "{input}")]
)
parser2 = StrOutputParser()
chain2 = prompt2 | model | parser2

# 串行组合：chain1 输出文本，用 lambda 转为 {"input": content}，以匹配 chain2 需要的输入结构
full_chain = chain1 | (lambda content: {"input": content}) | chain2

# 一次 invoke：先执行 chain1，再把结果作为 chain2 的 input
result = full_chain.invoke({"topic": "langchain"})
logger.info(result)

"""
【输出示例】
2026-03-06 10:24:22.765 | INFO     | __main__:<module>:38 - LangChain 是一个开源框架，用于构建基于大语言模型（LLM）的应用程序。它提供模块化组件（如链、代理、记忆、工具集成等），帮助开发者轻松连接 LLM 与外部数据源（如数据库、API）、实现对话状态管理、支持多步推理与工具调用，从而快速开发智能应用（如问答系统、AI 助手、自动化工作流）。核心理念是“编排”——将 LLM 作为通用接口，协同其他软件能力。
2026-03-06 10:24:27.723 | INFO     | __main__:<module>:53 - LangChain is an open-source framework for building applications powered by large language models (LLMs). It provides modular components—such as chains, agents, memory, and tool integrations—that help developers easily implement prompt engineering, external data integration (e.g., Retrieval-Augmented Generation, or RAG), multi-step reasoning, conversation state management, and more—thereby enhancing the controllability and practicality of LLM-powered applications.
"""
