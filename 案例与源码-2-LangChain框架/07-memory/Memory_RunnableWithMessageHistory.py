"""
【案例】内存版带历史对话：RunnableWithMessageHistory + InMemoryChatMessageHistory

对应教程章节：第 16 章 - 记忆与对话历史 → 6、案例代码 → 6.1 内存版（进程内，重启即丢失）

知识点速览：
- RunnableWithMessageHistory 在每次 invoke 时：先从 get_session_history(session_id) 取历史，拼入 prompt 的 MessagesPlaceholder，执行链后再把本轮输入与输出写回历史。
- InMemoryChatMessageHistory 把消息存在进程内存中，重启即丢失，适合单进程、无需持久化的场景。
- config 中 configurable={"session_id": "xxx"} 是 RunnableWithMessageHistory 的标准调用方式；本示例为了先讲清“最小可运行版本”，始终返回同一个 history，因此这里只演示单会话连续对话。
- 真正按 session_id 维护多份历史的写法见 Memory_RunnableWithMessageHistoryV2.py。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
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

# 提示模板：history 占位符用于注入历史消息，input 为当前用户输入
prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)
parser = StrOutputParser()
chain = prompt | llm | parser

# 记忆组件：内存实现，进程内有效，重启后丢失
history = InMemoryChatMessageHistory()

# 包装链为「带历史」版本：本例固定返回同一个 history，重点先放在“自动读写历史”
runnable = RunnableWithMessageHistory(
    chain,
    get_session_history=lambda session_id: history,
    input_messages_key="input",
    history_messages_key="history",
)
history.clear()
# 保留 session_id 配置，是为了让调用方式和 V2 / Redis 版保持一致
config = RunnableConfig(configurable={"session_id": "user-001"})

# 第一轮：写入「我叫张三，我爱好学习。」，模型回复后会自动写回 history
logger.info(runnable.invoke({"input": "我叫张三，我爱好学习。"}, config))
# 第二轮：history 中已有上一轮，模型能回答「叫什么、爱好是什么」
logger.info(runnable.invoke({"input": "我叫什么？我的爱好是什么？"}, config))

"""
【输出示例】
2026-03-09 15:00:07.626 | INFO     | __main__:<module>:55 - 你好，张三！很高兴认识一位热爱学习的朋友 😊
“爱好学习”是一种非常珍贵的品质——它意味着好奇心、成长型思维和对世界持续敞开的态度。无论你是在学习语言、编程、历史、艺术，还是探索生活中的新技能（比如做饭、摄影、心理学……），这份热情本身就值得赞赏！

如果你愿意分享，我很乐意陪你一起：
🔹 探讨某个具体的学习主题（比如“如何高效记英语单词”“零基础学Python怎么入门”）
🔹 制定一个小目标或学习计划
🔹 解答学习中遇到的困惑
🔹 或者只是聊聊你最近学到的、让你眼前一亮的一个小知识 🌟

继续加油，张三！学习路上，你不是一个人～ 📚✨
需要我帮你做点什么吗？
2026-03-09 15:00:11.848 | INFO     | __main__:<module>:57 - 你叫**张三**，你的爱好是**学习** 🌟
——这可是个闪闪发光的爱好！✨
（而且你刚刚还用行动证明了这一点：主动提问、清晰表达，本身就是学习力的体现呢 😄）

需要我帮你围绕“学习”做点什么吗？比如：
✅ 推荐适合初学者的自学资源
✅ 设计一个30天小习惯打卡计划
✅ 一起拆解某个你想学的知识点
✅ 或者……给你写一句专属学习座右铭？（比如：“张三所学，皆为光；日日精进，步步生莲。” 🌸）

随时告诉我～ 我在这儿支持你！ 📖🚀
"""
