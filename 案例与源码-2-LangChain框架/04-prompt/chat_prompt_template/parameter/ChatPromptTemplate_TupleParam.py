"""
【案例】用「元组 (role, content)」定义 ChatPromptTemplate 的消息

对应教程章节：第 13 章 - 提示词与消息模板 → 7、对话提示词模板（ChatPromptTemplate）

知识点速览：
- 元组写法是 `ChatPromptTemplate` 中最简洁、最常见的一种参数形式：`("角色", "内容")`。
- 它适合快速表达 system / human / ai 等角色关系，也很接近 `from_messages([...])` 的官方示例风格。
- 和字典、Message 类写法本质等价，更多是“表达风格不同”，不是“能力不同”。
"""

from langchain_core.prompts import ChatPromptTemplate

# 用「(role, content) 元组」的列表定义对话：system、human、ai、再一条 human（带占位符）
# chatPromptTemplate = ChatPromptTemplate(
chatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个AI开发工程师，你的名字是{name}。"),
        ("human", "你能帮我做什么?"),
        ("ai", "我能开发很多{thing}。"),
        ("user", "你能帮我做什么?"),
        ("assistant", "我能开发很多{thing}。"),
        ("human", "{user_input}"),
    ]
)

# 传入占位符变量，得到消息列表
prompt = chatPromptTemplate.format_messages(
    name="小谷AI", thing="AI", user_input="7 + 5等于多少"
)
print(prompt)

"""
【输出示例】
[SystemMessage(content='你是一个AI开发工程师，你的名字是小谷AI。', additional_kwargs={}, response_metadata={}), HumanMessage(content='你能帮我做什么?', additional_kwargs={}, response_metadata={}), AIMessage(content='我能开发很多AI。', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), HumanMessage(content='7 + 5等于多少', additional_kwargs={}, response_metadata={})]
"""
