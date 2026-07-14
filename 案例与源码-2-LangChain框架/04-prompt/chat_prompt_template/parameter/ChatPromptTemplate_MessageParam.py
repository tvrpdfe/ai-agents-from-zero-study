"""
【案例】用「消息模板类」定义 ChatPromptTemplate 的消息

对应教程章节：第 13 章 - 提示词与消息模板 → 7、对话提示词模板（ChatPromptTemplate）

知识点速览：
- 想让消息里的占位符 {name}、{question} 被真正替换，必须用「模板类」：`SystemMessagePromptTemplate`、`HumanMessagePromptTemplate`。
- 易踩坑：`SystemMessage`、`HumanMessage` 是「固定消息实例」，内容会原样输出，里面的 {name} 只是普通字符，format_messages() 不会替换它。
- 用 `.from_template("...")` 把带占位符的字符串包成消息模板，调用 format_messages() 时才会做变量替换。
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# 用消息模板类列表定义模板：系统消息 + 用户消息，内容里的占位符 {name}、{question} 会被替换
chat_prompt = ChatPromptTemplate(
    [
        SystemMessagePromptTemplate.from_template("你是AI助手，你的名字叫{name}。"),
        HumanMessagePromptTemplate.from_template("请问：{question}"),
    ]
)

# 传入占位符变量，得到消息列表
message = chat_prompt.format_messages(name="亮仔", question="什么是LangChain")
print(message)

# 同样的模板，用 from_messages 构造，效果与上面的构造器写法一致
chat_prompt1 = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("你是AI助手，你的名字叫{name}。"),
        HumanMessagePromptTemplate.from_template("请问：{question}"),
    ]
)

# 传入占位符变量，得到消息列表
message1 = chat_prompt1.format_messages(name="亮仔1", question="什么是LangChain")
print(message1)

"""
【输出示例】
[SystemMessage(content='你是AI助手，你的名字叫亮仔。', additional_kwargs={}, response_metadata={}), HumanMessage(content='请问：什么是LangChain', additional_kwargs={}, response_metadata={})]
"""
