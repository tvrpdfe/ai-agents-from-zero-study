"""
【案例】模型调用：异步 abatch（异步批量调用）

对应教程章节：第 13 章 - 提示词与消息模板 → 4、调用大模型的调用方式

知识点速览：
- `abatch` 是 `batch` 的异步版本，适合把批处理放进异步任务体系中统一调度。
- 用法是在 `async` 函数内 `await model.abatch(...)`；返回结果与 `batch` 一样，仍按输入顺序一一对应。
- 如果你当前只是想理解“批量调用”这个概念，先掌握同步版 `batch` 即可。
"""

import os
import asyncio
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

# abatch 本示例用「字符串列表」作为输入，无需单独导入 Message 类型

load_dotenv()

# ---------- 1. 实例化模型 ----------
model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---------- 2. 准备批量问题（与同步 batch 相同）----------
questions = [
    [
        SystemMessage(content="你是一个专业的助手。"),
        HumanMessage(content="什么是redis?简洁回答，字数控制在100以内"),
    ],
    [
        SystemMessage(content="你是一个专业的助手。"),
        HumanMessage(content="Python的生成器是做什么的？简洁回答，字数控制在100以内"),
    ],
    [
        SystemMessage(content="你是一个专业的助手。"),
        HumanMessage(
            content="解释一下Docker和Kubernetes的关系?简洁回答，字数控制在100以内"
        ),
    ],
]


# ---------- 3. 异步批量调用（在 async 函数中）----------
async def async_batch_call():
    # await model.abatch(questions)：异步批量处理，返回的仍是「问题与回答一一对应」的列表
    response = await model.abatch(questions)
    print(f"响应类型：{type(response)}")

    for q, r in zip(questions, response):
        print(f"问题：{q[1].content}\n回答：{r.content}\n")


# ---------- 4. 运行异步函数 ----------
if __name__ == "__main__":
    asyncio.run(async_batch_call())

"""
【输出示例】
响应类型：<class 'list'>
问题：什么是redis?简洁回答，字数控制在100以内
回答：Redis 是一个开源的、基于内存的高性能键值数据库，支持字符串、哈希、列表、集合等多种数据结构，提供持久化、主从复制、事务、发布/订阅等功能，常用于缓存、消息队列、会话存储等场景。

问题：Python的生成器是做什么的？简洁回答，字数控制在100以内
回答：Python生成器是一种惰性迭代器，用`yield`关键字定义，可逐个生成值而非一次性返回全部结果。它节省内存、支持无限序列，并在每次调用`next()`时暂停/恢复执行。

问题：解释一下Docker和Kubernetes的关系?简洁回答，字数控制在100以内
回答：Docker 是容器运行时，负责打包、构建和运行单个容器；Kubernetes（K8s）是容器编排平台，用于自动化部署、扩缩容、调度和管理大规模容器集群。Docker 为 Kubernetes 提供底层容器支持（如镜像和运行时），而 Kubernetes 可管理多个 Docker 容器（或其他兼容运行时，如 containerd）。二者常配合使用：Docker 构建镜像，K8s 编排运行。
"""
