"""
【案例】from_messages 创建模板 + format_messages / invoke / format 的用法

对应教程章节：第 13 章 - 提示词与消息模板 → 7、对话提示词模板（ChatPromptTemplate）

知识点速览：
- `from_messages([...])` 是创建 `ChatPromptTemplate` 的主流写法，最适合教学和实际项目阅读。
- `format_messages(...)` 返回消息列表，`invoke({...})` 返回 `ChatPromptValue`，`format(...)` 返回纯字符串。
- 真正发给聊天模型时，优先使用 `format_messages(...)` 或 `invoke({...})`，因为这两种方式能保留清晰的角色结构。
"""

from langchain_core.prompts import ChatPromptTemplate

# 用 from_messages 创建模板：一条 system（带 {role}）、一条 human（带 {question}）
chat_prompt = ChatPromptTemplate.from_messages(
    [("system", "你是一个{role}，请回答我提出的问题"), ("human", "请回答:{question}")]
)

# ---------- 方式一：format_messages ----------
# 下面两种写法完全等价，都是把 role、question 传给模板里的 {role}、{question}：
#   写法 A（关键字参数）：format_messages(role="python开发工程师", question="堆排序怎么写")
#   写法 B（字典 + ** 解包）：format_messages(**{"role": "python开发工程师", "question": "堆排序怎么写"})
# ** 表示把字典「解包」成 key=value 的形式传入，适合参数已经在 dict 里的场景。
prompt_value = chat_prompt.format_messages(
    **{"role": "python开发工程师", "question": "堆排序怎么写"}
)
print(prompt_value)

print()
# ---------- 方式二：invoke（传字典）----------
# 传入一个字典，键为占位符变量名，值为要填充的内容；返回的是 ChatPromptValue
# .to_string() 可把整段对话转成纯文本，方便打印查看
prompt_value2 = chat_prompt.invoke(
    {"role": "python开发工程师", "question": "堆排序怎么写"}
)
print(prompt_value2)
print(prompt_value2.to_string())
print(prompt_value2.to_messages())

print()

# ---------- 方式三：format（注意：返回的是字符串，不是消息列表）----------
# 适合只想得到「一整段文本」时用；若要把对话发给聊天模型，请用 format_messages 或 invoke
prompt_value3 = chat_prompt.format(
    **{"role": "python开发工程师", "question": "快速排序怎么写"}
)
print(prompt_value3)


# 如果后续要真正调用模型，可把 format_messages(...) 的结果或 invoke(...) 的返回值继续交给 model.invoke(...)

"""
【输出示例】
[SystemMessage(content='你是一个python开发工程师，请回答我提出的问题', additional_kwargs={}, response_metadata={}), HumanMessage(content='请回答:堆排序怎么写', additional_kwargs={}, response_metadata={})]

System: 你是一个python开发工程师，请回答我提出的问题
Human: 请回答:堆排序怎么写

System: 你是一个python开发工程师，请回答我提出的问题
Human: 请回答:快速排序怎么写
"""
