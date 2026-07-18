"""
【案例】Redis 持久化对话历史：RunnableWithMessageHistory + RedisChatMessageHistory

对应教程章节：第 16 章 - 记忆与对话历史 → 6、案例代码 → 6.2 持久化：Redis 存储 → Redis 对话历史示例

知识点速览：
- 这个案例和内存版的核心链路没有变化，变化的只是 get_session_history(...) 返回的存储后端：从 InMemoryChatMessageHistory 换成 RedisChatMessageHistory。
- RunnableWithMessageHistory 负责“什么时候读写历史”，RedisChatMessageHistory 负责“历史存到哪里”；两者是配合关系，不是替代关系。
- 项目依赖更推荐使用 langchain-redis；若本地环境仍只有 langchain-community，本示例会自动回退，便于旧环境继续运行。
- 默认连接 redis://localhost:6379，可通过环境变量 REDIS_URL 覆盖；如果你用的是 Redis Stack 的宿主机映射端口，可设 REDIS_URL=redis://localhost:26379。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain.chat_models import init_chat_model
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
import os
import redis
from loguru import logger

try:
    from langchain_redis import RedisChatMessageHistory

    USE_LANGCHAIN_REDIS = True
except ModuleNotFoundError:
    from langchain_community.chat_message_histories import RedisChatMessageHistory

    USE_LANGCHAIN_REDIS = False

# 支持环境变量 REDIS_URL；未设置时默认 localhost:6379（标准 Redis），教程 Docker 可能用 26379
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
FORCE_SAVE = os.getenv("REDIS_FORCE_SAVE", "0") == "1"


def _check_redis():
    """启动时检查 Redis 是否可达，不可达时给出明确提示后退出。"""
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        r.close()
    except (redis.ConnectionError, redis.ResponseError) as e:
        logger.error(
            "Redis 连接失败（{}）。请先启动 Redis，例如：\n"
            "  docker run -d -p 6379:6379 redis\n"
            "若使用其他端口，可设置环境变量：REDIS_URL=redis://localhost:端口",
            REDIS_URL,
        )
        raise SystemExit(1) from e


_check_redis()

# 原生 Redis 客户端，decode_responses=True 使返回值为 str 而非 bytes
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
logger.info(
    "Redis 历史实现：{} | REDIS_URL={}",
    "langchain-redis" if USE_LANGCHAIN_REDIS else "langchain-community（兼容回退）",
    REDIS_URL,
)

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
    """为每个 session_id 创建/返回对应的 Redis 历史实例，实现持久化存储。"""
    if USE_LANGCHAIN_REDIS:
        return RedisChatMessageHistory(
            session_id=session_id,
            redis_url=REDIS_URL,
        )
    return RedisChatMessageHistory(
        session_id=session_id,
        url=REDIS_URL,
    )


chain = RunnableWithMessageHistory(
    prompt | llm,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)
config = RunnableConfig(configurable={"session_id": "user-001"})

print("开始对话（输入 'quit' 退出）")
while True:
    question = input("\n输入问题：")
    if question.lower() in ["quit", "exit", "q"]:
        break
    response = chain.invoke({"question": question}, config)
    logger.info(f"AI回答:{response.content}")
    # 可选：把 Redis 当前内存快照刷到磁盘，方便演示“Redis 重启后仍能恢复”。
    # 这不是多轮记忆生效的必要条件，真实项目也不建议在每轮对话后都手动 SAVE。
    if FORCE_SAVE:
        redis_client.save()

"""
【输出示例】
开始对话（输入 'quit' 退出）
"""

# 输入问题：你好
# 2026-03-09 15:48:12.211 | INFO     | __main__:<module>:82 - AI回答:你好！很高兴见到你～😊 有什么我可以帮你的吗？无论是学习、工作、生活中的问题，还是想聊聊天、获取信息、一起动脑筋，我都很乐意帮忙！

# 输入问题：我叫黎明
# 2026-03-09 15:48:18.845 | INFO     | __main__:<module>:82 - AI回答:你好，黎明！✨ 很高兴认识你～这个名字真有诗意，让人联想到晨光初现、万物苏醒的温柔时刻 🌅
# 希望我们接下来的交流也能像黎明一样，带来清晰、温暖和一点点小期待 😊

# 你今天过得怎么样？或者有什么想聊的、想问的、想一起探索的？我在这儿认真听着呢～ 🌟

# 输入问题：我叫什么
# 2026-03-09 15:48:24.063 | INFO     | __main__:<module>:82 - AI回答:你叫**黎明** ✨
# ——这个名字我记住了，而且很喜欢它蕴含的光与希望感 🌅

# 需要我帮你做点什么吗？比如：
# 🔹 起个昵称或笔名（呼应“黎明”主题）
# 🔹 写一句专属的晨光小诗
# 🔹 规划一个清晨习惯计划
# 🔹 或者……单纯陪你聊聊今天的“光”在哪里？

# 随时告诉我～ 🌟

# 输入问题：redis-cli -h 127.0.0.1 -p 6379 PING
# 2026-03-09 15:48:49.818 | INFO     | __main__:<module>:82 - AI回答:你执行的是 Redis 的连通性测试命令：

# ```bash
# redis-cli -h 127.0.0.1 -p 6379 PING
# ```

# ✅ **预期正常响应是：**
# ```
# PONG
# ```

# 这表示：
# - Redis 服务正在本地（`127.0.0.1`）运行；
# - 端口 `6379` 可访问；
# - 客户端能成功连接并通信。

# ---
