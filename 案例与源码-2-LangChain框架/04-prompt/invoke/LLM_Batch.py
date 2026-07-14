"""
【案例】模型调用：同步 batch（批量调用）

对应教程章节：第 13 章 - 提示词与消息模板 → 4、调用大模型的调用方式

知识点速览：
- `batch` 适合一次处理多条彼此独立的输入，常见于离线任务、批量评估、数据清洗等场景。
- 返回值是与输入顺序一一对应的结果列表；列表中每一项通常仍是 `AIMessage`。
- 本案例用“字符串列表”演示最简单的批量输入；如果要做多角色批量，也可以传“消息列表的列表”。
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# 本示例用「字符串列表」作为 batch 输入，无需 Message 类型；若改为多角色可引入 HumanMessage、SystemMessage

load_dotenv()

# ---------- 1. 实例化模型 ----------
model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---------- 2. 准备多条独立问题（批量输入的列表）----------
# 每一条字符串会作为「一次请求」发给模型；batch 会并行处理这些请求，最后返回与之一一对应的响应列表。
questions = [
    "什么是redis?简洁回答，字数控制在100以内",
    "Python的生成器是做什么的？简洁回答，字数控制在100以内",
    "解释一下Docker和Kubernetes的关系?简洁回答，字数控制在100以内",
]

# ---------- 3. 批量调用：model.batch(questions) ----------
# 返回的是一个列表，每个元素对应一条问题的 AIMessage，用 .content 取该条回复的文本。
response = model.batch(questions)
print(f"响应类型：{type(response)}")
print()

# zip(questions, response)：把“问题列表”和“回答列表”按位置配对，便于一起遍历。
for q, r in zip(questions, response):
    print(f"问题：{q}\n回答：{r.content}\n")

"""
【输出示例】    
响应类型：<class 'list'>
问题：什么是redis?简洁回答，字数控制在100以内
回答：Redis 是一个开源的、基于内存的高性能键值数据库，支持字符串、哈希、列表、集合等多种数据结构，提供持久化、主从复制、事务、发布/订阅等功能，常用于缓存、消息队列、会话存储等场景。

问题：Python的生成器是做什么的？简洁回答，字数控制在100以内
回答：Python生成器是一种惰性迭代器，用`yield`关键字定义，可逐个生成值而非一次性返回全部结果，节省内存。调用时返回生成器对象，支持`next()`或`for`循环遍历，适合处理大数据流或无限序列。

问题：解释一下Docker和Kubernetes的关系?简洁回答，字数控制在100以内
回答：Docker 是容器运行时，负责打包、构建和运行单个容器；Kubernetes（K8s）是容器编排平台，用于自动化部署、扩缩容、调度和管理大规模容器集群。K8s 可以使用 Docker 作为底层容器运行时（现更多用 containerd），但两者职责不同：Docker 关注“如何运行一个容器”，K8s 关注“如何管理成百上千个容器”。
"""
