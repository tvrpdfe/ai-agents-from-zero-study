"""
【案例】内存版带历史对话（多 session）：用 store 按 session_id 维护多份 InMemoryChatMessageHistory

对应教程章节：第 16 章 - 记忆与对话历史 → 6、案例代码 → 6.1 内存版（进程内，重启即丢失）

知识点速览：
- 与 Memory_RunnableWithMessageHistory 的区别：本案例用 get_session_history(session_id) 从 store 中按 session 取不同 history，可支持多用户/多会话（每 session 独立历史）。
- MessagesPlaceholder("history") 与 prompt 中的变量名一致，RunnableWithMessageHistory 会把读到的历史注入此处；input_messages_key、history_messages_key 需与 prompt 占位符对应。
- 本案例会同时演示 user-001 与 user-002 两个 session，帮助你直观看到“同一套链逻辑，如何切换到不同历史”。
- 生产环境可将 store 换成 Redis、数据库等，get_session_history 返回 RedisChatMessageHistory(session_id=session_id, ...) 即可实现持久化（见 6.2）。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain.chat_models import init_chat_model
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import os

llm = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 按 session_id 保存多份历史，便于多用户/多会话；生产可改为 Redis 等
store = {}


def get_session_history(session_id: str):
    """
    根据 session_id 获取对应的历史消息对象。
    如果不存在则创建一个新的 InMemoryChatMessageHistory。
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# 定义 Prompt 模板
#     - system: 给模型设定角色
#     - MessagesPlaceholder: 历史消息将注入这里
#     - human: 当前用户输入
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个友好的中文助理，会根据上下文回答问题。"),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)
# 构建基本链：Prompt → LLM → 输出解析
memory_chain = prompt | llm | StrOutputParser()

# 包装为带历史链：get_session_history 决定「当前 session 用哪份 history」
with_history = RunnableWithMessageHistory(
    memory_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

cfg_user_001 = {"configurable": {"session_id": "user-001"}}
cfg_user_002 = {"configurable": {"session_id": "user-002"}}

print("用户A（user-001）：我叫张三。")
print("AI：", with_history.invoke({"question": "我叫张三。"}, cfg_user_001))

print("\n用户B（user-002）：我叫李四。")
print("AI：", with_history.invoke({"question": "我叫李四。"}, cfg_user_002))

print("\n用户A（user-001）：我叫什么？")
print("AI：", with_history.invoke({"question": "我叫什么？"}, cfg_user_001))

print("\n用户B（user-002）：我叫什么？")
print("AI：", with_history.invoke({"question": "我叫什么？"}, cfg_user_002))

# ---------- 查看当前存储了哪些历史数据 ----------
# store 的 key 为 session_id，value 为该会话的 InMemoryChatMessageHistory
# 每个 history 的 .messages 为 List[BaseMessage]，即该会话至今的全部消息（HumanMessage、AIMessage 等）
print("\n--- 当前 store 中的历史数据 ---")
for sid, history in store.items():
    print(f"[session_id={sid}] 共 {len(history.messages)} 条消息:")
    for i, msg in enumerate(history.messages):
        # msg 有 .type（如 human/ai）、.content（文本内容）
        content = str(msg.content)
        content_preview = (content[:50] + "…") if len(content) > 50 else content
        print(f"  {i+1}. [{msg.type}] {content_preview}")
print("--- 以上 ---\n")

"""
【输出示例】
用户A（user-001）：我叫张三。
AI： 你好，张三！很高兴认识你～😊  
有什么我可以帮你的吗？

用户B（user-002）：我叫李四。
AI： 你好，李四！很高兴认识你～😊  
有什么我可以帮你的吗？

用户A（user-001）：我叫什么？
AI： 你叫张三！😄  
之前你已经告诉过我啦～需要我帮你做点什么吗？

用户B（user-002）：我叫什么？
AI： 你叫李四！😄  
之前你已经告诉过我啦～需要我帮你做点什么吗？

--- 当前 store 中的历史数据 ---
[session_id=user-001] 共 4 条消息:
  1. [human] 我叫张三。
  2. [ai] 你好，张三！很高兴认识你～😊  
有什么我可以帮你的吗？
  3. [human] 我叫什么？
  4. [ai] 你叫张三！😄  
之前你已经告诉过我啦～需要我帮你做点什么吗？
[session_id=user-002] 共 4 条消息:
  1. [human] 我叫李四。
  2. [ai] 你好，李四！很高兴认识你～😊  
有什么我可以帮你的吗？
  3. [human] 我叫什么？
  4. [ai] 你叫李四！😄  
之前你已经告诉过我啦～需要我帮你做点什么吗？
--- 以上 ---

"""
