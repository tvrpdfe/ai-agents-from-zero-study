"""
【案例】LangChain 1.0 写法：init_chat_model 统一入口调用大模型

对应教程章节：第 10 章 - LangChain 快速上手与 HelloWorld → 4、实战：基于阿里百炼的 HelloWorld

知识点速览：
- 1.0 推荐用 init_chat_model 作为统一入口，通过 model_provider（如 "openai"）指定厂商，同一套写法可切换模型。
- 接国内平台（阿里百炼、通义等）时需显式写 model_provider="openai"，否则会报错无法推断 provider。
- 调用三件套：API Key、模型名、Base URL；invoke(问题) 返回消息对象，.content 取正文。
"""

# ========== 1. 导入依赖 ==========
import os
from dotenv import load_dotenv
from langchain.chat_models import (
    init_chat_model,
)  # 1.0 统一入口：根据 model + model_provider 创建聊天模型

load_dotenv(encoding="utf-8")

# ========== 2. 实例化模型并调用 ==========
# 关键字参数：k1=v1, k2=v2 的形式（比如这种写法：model="qwen-plus"，就是关键字参数），顺序可打乱，可读性更好
model = init_chat_model(
    model="deepseek-v4-flash",  # 模型 ID
    model_provider="openai",  # 表示使用「OpenAI 兼容」的 API
    api_key=os.getenv(
        "DEEPSEEK_API_KEY"
    ),  # 需事先 export 或在下面 load_dotenv 之后再用
    base_url="https://api.deepseek.com",
    reasoning_effort="low",
)

# 调用并直接取回复正文：invoke 返回消息对象，.content 为文本内容
print(model.invoke("你是谁").content)

print("*" * 50)

# 若不写 model_provider="openai"，会报错：
# ValueError: Unable to infer model provider for model='qwen-plus', please specify model_provider directly.
# 原因：qwen-plus 等名称无法自动推断厂商，必须显式指定。
# 对比 0.3：0.3 用 ChatOpenAI 类，类名已表示「OpenAI 兼容」，故无需 model_provider。

# 同一个系统里面，可以同时存在多个模型，比如
model2 = init_chat_model(
    model="deepseek-v4-pro",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    reasoning_effort="low",
)

print(model2.invoke("你是谁").content)

"""
【输出示例】
你好！我是通义千问（Qwen），阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，比如写故事、写公文、写邮件、写剧本、逻辑推理、编程等等，还能表达观点，玩游戏等。如果你有任何问题或需要帮助，欢迎随时告诉我！😊
**************************************************
我是DeepSeek Chat，由深度求索公司打造的AI助手！🤖✨ 我可以帮你回答问题、提供建议、聊天解闷，还能处理各种文本和文件信息。有什么我可以帮你的吗？😊
"""
