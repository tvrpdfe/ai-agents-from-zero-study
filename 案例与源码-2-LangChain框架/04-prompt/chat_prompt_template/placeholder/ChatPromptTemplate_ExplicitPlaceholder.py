"""
【案例】显式使用 MessagesPlaceholder：在模板里预留一段消息的位置

对应教程章节：第 13 章 - 提示词与消息模板 → 7.5、MessagesPlaceholder：消息占位符

知识点速览：
- `MessagesPlaceholder` 的作用，是在模板里先预留一段“消息列表的位置”，等调用时再把历史对话整块插进去。
- 这特别适合多轮对话、记忆、上下文拼接等场景，因为历史消息条数往往不是写模板时就固定好的。
- 显式写法是 `MessagesPlaceholder("memory")`；调用时传入的字典键必须与这里的变量名一致。
"""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 模板：系统消息 + 一个「消息占位符」memory + 当前用户问题 {question}
# memory 位置会在 invoke 时被替换成你传入的消息列表（如历史对话）
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个资深的Python应用开发工程师，请认真回答我提出的Python相关的问题",
        ),  # role 须为标准名：system / human / ai（不可自创如 system1）；也可写 SystemMessage(content="...")
        MessagesPlaceholder(
            "memory"
        ),  # 变量名可自取，如 "history"、"chat_history" 等，invoke 时键与之一致即可
        ("human", "{question}"),
    ]
)

# invoke 时传入：memory = 历史消息列表，question = 当前问题
# 这里用两条消息模拟「上一轮」的对话，再问「我的名字叫什么」来测试模型是否利用上下文
# prompt_value = prompt.invoke(
#     {
#         "memory": [
#             HumanMessage("我的名字叫亮仔，是一名程序员111"),
#             AIMessage("好的，亮仔你好222"),
#         ],
#         "question": "请问我的名字叫什么？",
#     }
# )

prompt_value = prompt.format_messages(
    memory=[
        HumanMessage("我的名字叫亮仔，是一名程序员111"),
        AIMessage("好的，亮仔你好222"),
    ],
    question="请问我的名字叫什么？",
)

# 把整段 prompt 转成字符串查看（系统设定 + 历史 + 当前问题）
# print(prompt_value.to_string())
print(prompt_value)

"""
【输出示例】
System: 你是一个资深的Python应用开发工程师，请认真回答我提出的Python相关的问题
Human: 我的名字叫亮仔，是一名程序员111
AI: 好的，亮仔你好222
Human: 请问我的名字叫什么？
"""
