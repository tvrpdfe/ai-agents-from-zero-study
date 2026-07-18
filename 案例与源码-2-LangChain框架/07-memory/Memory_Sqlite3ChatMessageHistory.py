"""
【案例】SQLite 持久化对话历史：RunnableWithMessageHistory + SQLChatMessageHistory

对应教程章节：第 16 章 - 记忆与对话历史 → 6、案例代码 → 6.2 持久化存储

知识点速览：
- 这个案例和 Redis 版的核心链路没有变化，变化的只是 get_session_history(...) 返回的存储后端：从 RedisChatMessageHistory 换成 SQLChatMessageHistory（底层用 SQLite 文件）。
- RunnableWithMessageHistory 负责“什么时候读写历史”，SQLChatMessageHistory 负责“历史存到哪里”；两者是配合关系，不是替代关系。
- 数据库文件默认写在本脚本同级目录下的 chat_history.db，进程重启后同一 session_id 仍可恢复对话。
- 依赖：langchain-community（内含 SQLChatMessageHistory）+ sqlalchemy；SQLite 本身是 Python 标准库，无需单独安装数据库服务。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from pathlib import Path
import os

from langchain.chat_models import init_chat_model
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_community.chat_message_histories import SQLChatMessageHistory
from loguru import logger

# 数据库文件放在本脚本同级目录；可通过环境变量 SQLITE_DB_PATH 覆盖
_DEFAULT_DB_PATH = Path(__file__).resolve().parent / "chat_history.db"
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(_DEFAULT_DB_PATH))).resolve()
# SQLAlchemy 连接串：sqlite:/// 后接绝对路径时在 Windows 上需写成 sqlite:///C:/... 形式
CONNECTION = f"sqlite:///{DB_PATH.as_posix()}"

logger.info("SQLite 历史数据库：{}", DB_PATH)

llm = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
prompt = ChatPromptTemplate.from_messages(
    [MessagesPlaceholder("history"), ("human", "{question}")]
)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """为每个 session_id 创建/返回对应的 SQLite 历史实例，实现持久化存储。"""
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=CONNECTION,
    )


chain = RunnableWithMessageHistory(
    prompt | llm,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)
config = RunnableConfig(configurable={"session_id": "user-001"})

print("开始对话（输入 'quit' 退出）")
print(f"对话历史将持久化到：{DB_PATH}")
while True:
    question = input("\n输入问题：")
    if question.lower() in ["quit", "exit", "q"]:
        break
    response = chain.invoke({"question": question}, config)
    logger.info(f"AI回答:{response.content}")

"""
【输出示例】
开始对话（输入 'quit' 退出）
对话历史将持久化到：.../07-memory/chat_history.db

输入问题：你好
AI回答:你好！很高兴见到你～有什么我可以帮你的吗？

输入问题：我叫黎明
AI回答:你好，黎明！很高兴认识你～

输入问题：我叫什么
AI回答:你叫黎明。

# 退出后再重新运行本脚本，同一 session_id=user-001 仍能从 chat_history.db 读回历史。
"""
