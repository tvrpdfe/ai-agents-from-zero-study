"""
【案例】模型调用：异步 astream（异步流式输出）

对应教程章节：第 13 章 - 提示词与消息模板 → 4、调用大模型的调用方式

知识点速览：
- `astream` 是 `stream` 的异步版本，适合异步服务里的流式输出。
- 它返回的是异步生成器，因此必须用 `async for` 遍历，而不是普通 `for`。
- 循环中的每一块通常仍是 `AIMessageChunk`，只是读取方式变成了异步。
"""

import os
import asyncio
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

load_dotenv()

# ---------- 1. 实例化模型 ----------
model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---------- 2. 构建多角色消息 ----------
messages = [
    SystemMessage(content="你是一个获奖无数的作家"),
    HumanMessage(content="写一篇800字左右的黑暗童话"),
]


# ---------- 3. 异步流式调用（在 async 函数中）----------
async def async_stream_call():
    # astream(messages) 返回的是「异步生成器」，不是 await 一个整体结果
    response = model.astream(messages)
    print(f"响应类型：{type(response)}")  # <class 'async_generator'>

    # 必须用 async for 遍历异步生成器，不能用普通 for
    async for chunk in response:
        print(chunk.content, end="", flush=True)
    print("\n")


# ---------- 4. 运行异步函数 ----------
if __name__ == "__main__":
    asyncio.run(async_stream_call())

"""
【输出示例】
响应类型：<class 'async_generator'>
你好呀！我是小问，一个乐于助人的AI人工助手～😊
我擅长解答问题、帮你理清思路、写文案、做学习规划、整理资料，甚至陪你聊聊天、出出主意。不管是学习上的难题、工作中的困惑，还是生活里的小烦恼，我都很乐意倾听和帮忙！
"""
