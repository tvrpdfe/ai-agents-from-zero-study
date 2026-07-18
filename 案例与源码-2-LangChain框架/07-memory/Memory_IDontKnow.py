"""
【案例】「我不知道」演示：无记忆时两轮请求相互独立，模型无法利用上一轮内容

对应教程章节：第 16 章 - 记忆与对话历史 → 3、「我不知道」演示：无记忆时的行为

知识点速览：
- 若只用「Prompt + Model + Parser」且不保存历史，每次 invoke 相互独立，模型看不到上一轮对话。
- 本案例先问「我叫张三，你叫什么?」，再问「你知道我是谁吗?」——第二问时模型会回答「我不知道」，因为程序没有把第一轮内容注入到第二轮。
- 对比：网页版聊天能记住多轮内容，是因为前端或后端实现了历史记忆（读历史 → 拼入提示 → 写回历史）；本章后续案例用 RunnableWithMessageHistory + 记忆组件实现该能力。
"""

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
import os

# 大模型与简单链：仅「提示模板 → 模型 → 解析器」，无任何记忆组件
llm = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
prompt = PromptTemplate.from_template("请回答我的问题：{question}")
parser = StrOutputParser()
chain = prompt | llm | parser

# 第一轮：告诉模型「我叫张三」
print(chain.invoke({"question": "我叫张三，你叫什么?"}))

# 第二轮：问「你知道我是谁吗？」——模型无法看到上一轮，会回答「我不知道」
print(chain.invoke({"question": "你知道我是谁吗?"}))

"""
你好，张三！我叫通义千问（Qwen），是阿里云研发的超大规模语言模型。很高兴认识你！😊
我不知道你是谁。我是一个AI助手，没有能力识别或获取用户的身份信息。如果你有任何问题需要帮助，我会很乐意为你提供支持！

解释：
我们刚刚在本地程序，前一轮对话告诉大语言模型的信息，下一轮就被“遗忘了”。
但如果我们直接使用网页版聊天工具，它之所以能记住多轮内容，是因为应用层实现了历史记忆功能，而不是模型参数在本地被改写。
"""

"""
【输出示例】
你好，张三！😊 我是通义千问（Qwen），是阿里巴巴集团旗下的超大规模语言模型。你可以叫我通义千问，或者亲切地叫我小Q～
很高兴认识你！有什么问题、需要帮忙写文案、学习辅导、编程支持，或者只是想聊聊天，我都很乐意陪你～ 🌟
你好！😊 我并不知道你是谁——我没有访问个人身份信息的能力，也不会记住或识别用户的身份（除非你在当前对话中主动告诉我一些信息）。我是通义千问（Qwen），一个AI助手，专注于理解你的问题、提供有用的信息和真诚的交流。
"""

# 如果你愿意，可以告诉我你的名字、兴趣，或者你正在思考的问题——我很乐意以更个性化的方式和你互动！✨
