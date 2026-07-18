"""
【案例】直接使用 InMemoryChatMessageHistory 的 API：add_message、messages，手动拼历史后调用模型

对应教程章节：第 16 章 - 记忆与对话历史 → 5、实现类介绍（BaseChatMessageHistory 与常用实现）/ 6.1 内存版

知识点速览：
- BaseChatMessageHistory 的实现类提供 add_message(msg)、add_user_message(text)、messages（只读列表）等；本案例演示不通过 RunnableWithMessageHistory，而是手动维护 history 并每次把 history.messages 传给 llm.invoke。
- 手动维护 history 时，要自己决定“什么时候把用户消息写进去、什么时候把 AI 回复写回去”；如果漏掉 add_message(ai_message)，下一轮模型就看不到自己的上一轮回答。
- 适用场景：需要细粒度控制「何时写入历史、何时读取」时，可直接操作 history；多数场景更推荐用 RunnableWithMessageHistory 自动完成「读→拼入→执行→写回」。
- 内存版：数据仅在进程内，重启即丢失；持久化见 6.2 RedisChatMessageHistory。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain.chat_models import init_chat_model
from langchain_core.chat_history import InMemoryChatMessageHistory
from loguru import logger
import os

llm = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 创建内存版历史实例（BaseChatMessageHistory 的实现）
history = InMemoryChatMessageHistory()

# 手动添加用户消息并调用模型；模型输入为当前全部 messages
history.add_user_message("我叫张三，我的爱好是学习")
ai_message = llm.invoke(history.messages)
logger.info(f"第一次回答\n{ai_message.content}")
# 手动把 AI 回复写回 history；否则下一轮只会看到用户消息，达不到“多轮记忆”的效果
history.add_message(ai_message)

# 再追加一轮：用户问「我叫什么？我的爱好是什么？」；此时 history.messages 已含上一轮
history.add_user_message("我叫什么？我的爱好是什么？")
ai_message2 = llm.invoke(history.messages)
logger.info(f"第二次回答\n{ai_message2.content}")
# 这一轮的 AI 回复也同样需要手动写回
history.add_message(ai_message2)

# 遍历当前会话全部消息；可以直观看到 history.messages 本质上就是一组 BaseMessage
for index, message in enumerate(history.messages, start=1):
    logger.info(f"第{index}条[{message.type}] {message.content}")

"""
【输出示例】
2026-03-09 15:17:53.046 | INFO     | __main__:<module>:35 - 第一次回答
你好，张三！很高兴认识你……
2026-03-09 15:17:55.429 | INFO     | __main__:<module>:41 - 第二次回答
你叫张三，你的爱好是学习……
2026-03-09 15:17:55.429 | INFO     | __main__:<module>:46 - 第1条[human] 我叫张三，我的爱好是学习
2026-03-09 15:17:55.429 | INFO     | __main__:<module>:46 - 第2条[ai] 你好，张三！很高兴认识你……
2026-03-09 15:17:55.429 | INFO     | __main__:<module>:46 - 第3条[human] 我叫什么？我的爱好是什么？
2026-03-09 15:17:55.429 | INFO     | __main__:<module>:46 - 第4条[ai] 你叫张三，你的爱好是学习……
"""
