# 10 - 深度研搜：网络搜索子智能体与 Tavily 工具

---

**本章课程目标：**

- 理解 DeepAgents 子智能体的三个核心组成：描述、提示词、工具。
- 完成 `internet_search` 工具封装，并接入 Tavily 搜索能力。
- 理解两种向前端推送进度的方式：流式解析和工具内部埋点。
- 组装 `network_search_agent`，让它成为主智能体后续可以调度的专家助手。

**学习建议：** 网络搜索助手是最适合入门的子智能体，因为它不涉及数据库结构，也不涉及 RAGFlow 的平台层级。读本章时重点看一个子智能体字典里到底放了什么：名称、职责描述、提示词、工具。能把 Tavily 换成别的搜索工具并说清要改哪里，就说明这章吃透了。

**对应代码分支：** `10-deepsearch-network-subagent`

---

从本章开始，我们正式进入子智能体实现阶段。整个「深度研搜」项目会陆续实现 3 个专家助手：

| 子智能体       | 负责内容                       | 本章是否实现 |
| -------------- | ------------------------------ | ------------ |
| 网络搜索助手   | 查询互联网公开资料和最新信息   | 是           |
| 数据库查询助手 | 查询企业内部结构化业务数据     | 否，下一章   |
| RAGFlow 助手   | 查询企业内部非结构化知识库文档 | 否，后续章节 |

网络搜索助手是第一个要写的子智能体。它的底层工具很简单：调用 Tavily，根据关键词搜索公开网页资料。

本章的重点是掌握子智能体的固定写法：

```text
子智能体 = 描述 description + 系统提示词 system_prompt + 工具 tools
```

这个套路学会以后，后面写数据库助手、RAGFlow 助手，思路就顺了：先写清职责边界，再给它能用的工具，最后组装成主智能体可以调度的配置。

---

## 1、网络搜索子智能体要写哪三件事

第 9 章已经讲过 `name`、`description`、`system_prompt` 的区别。本章不再重复定义概念，直接看它们落到网络搜索助手时应该怎么写。

### 1.1 description：写清“什么时候找我”

网络搜索助手的 `description` 要解决的是路由问题：主智能体看到用户任务后，能不能判断该不该把任务交给它。

比如用户问：

```text
查询 2025 年某医药政策的最新公开信息。
```

这类问题需要外部公开资料，应该交给网络搜索助手。

但如果用户问：

```text
查询公司数据库里布洛芬的库存。
```

这类问题属于内部业务数据，不应该交给网络搜索助手，而应该交给数据库查询助手。

所以这里的描述重点不是“我会搜索”，而是写清边界：**只处理互联网公开信息，不处理数据库数据，也不处理 RAGFlow 私有知识库内容。**

### 1.2 system_prompt：写清“怎么搜索”

`system_prompt` 要约束网络搜索助手自己的执行方式。对这个助手来说，最重要的是两件事：搜索要有覆盖面，搜索次数要有上限。

| 约束                | 作用                       |
| ------------------- | -------------------------- |
| 至少从 3 个角度检索 | 避免只搜一个关键词就结束   |
| 最多搜索 5 次       | 避免无限调用工具造成死循环 |

这两个限制放在提示词里，比只写“请认真搜索”更可靠。前者能提醒模型换关键词、换角度查资料，后者能避免它在结果不理想时反复调用工具。

### 1.3 tools：接入真正的搜索能力

`description` 和 `system_prompt` 只负责告诉模型“该不该做”和“怎么做”，真正访问互联网还要靠工具。

本章给网络搜索助手配置一个工具：

| 工具名            | 作用                                               |
| ----------------- | -------------------------------------------------- |
| `internet_search` | 使用 Tavily 查询互联网公开信息，返回结构化搜索结果 |

后面主智能体调用网络搜索助手时，网络搜索助手会再调用 `internet_search`，由 Tavily 完成真实网页检索。

---

## 2、完善 prompts.yml 中的网络助手配置

项目对应文件路径：`deepsearch-agents/app/prompt/prompts.yml`

在第 9 章，我们已经把提示词放进 YAML 文件统一管理。现在先补全网络搜索助手的配置。

```yaml
# DeepAgents 提示词配置：集中管理主智能体和各子智能体的名称、路由描述与系统提示词
# 主智能体读取 description 做任务分派，子智能体读取 system_prompt 约束自己的执行方式

# 子智能体配置：description 给主智能体判断是否调用，system_prompt 给子智能体约束执行方式
sub_agents:
  # 网络搜索助手只处理互联网公开信息；数据库和 RAGFlow 私有知识库由其他助手负责
  tavily:
    name: "网络搜索助手"
    description: |
      负责进行网络知识搜索的智能体助手，当需要从网络中查询数据的时候，可以执行数据检索，在检索后会返回一段检索结果。
      注意：在需要进行非内部信息，不是数据库数据和 RAGFlow 知识库数据的公开信息查询时，务必使用此助手进行查询。
    system_prompt: |
      你是一个专业的网络信息查询助手，你可以根据用户的问题，从互联网中检索相关信息。
      你掌握的工具包括 internet_search 工具，此工具可以根据用户的问题，从互联网中检索非内部的公开信息。
      在检索网络知识的时候，至少检索 3 个角度的该问题，一共最多进行 5 次检索，如果超过 5 次，则不允许继续检索。
```

读这段配置时，先抓住一个边界：**网络搜索助手只负责外部公开信息。** 用户问数据库里的药品销量，应该交给数据库助手；用户问企业内部手册、制度、文档，应该交给 RAGFlow 助手。边界写清楚，后面主智能体调度才会稳定。

---

## 3、准备 Tavily 配置

### 3.1 .env 中加入 Tavily Key

项目对应文件路径：`deepsearch-agents/.env`

添加 Tavily 配置：

```dotenv
TAVILY_API_KEY=your-tavily-api-key
```

这里的 Key 需要先到 Tavily 控制台注册并创建。浏览器打开：https://app.tavily.com/home

注册或登录后，在控制台中创建 API Key，再把生成的 Key 填到 `.env` 的 `TAVILY_API_KEY` 后面。

### 3.2 为什么使用 Tavily

Tavily 是面向大模型使用的搜索 API，它返回的结果通常已经整理成结构化字段，比较适合 Agent 继续阅读和总结。

在这个项目里，网络搜索助手主要用它处理这些任务：

- 查询公开资料；
- 查询最新新闻或政策；
- 查询外部背景信息；
- 给主智能体补充企业内部资料之外的上下文。

---

## 4、实现并验证 internet_search 工具

项目对应文件路径：`deepsearch-agents/app/tools/tavily_tool.py`

完整工具可以先按五段理解：

1. 导入依赖和加载 `.env`。
2. 创建 `TavilyClient`。
3. 用 `@tool` 把普通函数注册成 Agent 可以调用的工具。
4. 在工具内部调用 `monitor.report_tool(...)`，把搜索参数推给前端。
5. 提供 `__main__` 本地调试入口，方便先验证 Key 和 Tavily API 是否可用。

核心代码如下：

```python
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

from app.api.monitor import monitor

load_dotenv()


# TavilyClient 是实际访问搜索服务的客户端；模块级复用可避免每次工具调用重复初始化
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# @tool 会把函数签名和 docstring 暴露给 DeepAgents，模型据此决定是否调用以及如何填参
@tool
def internet_search(
    query: str,
    topic: Literal["news", "finance", "general"] = "general",
    max_results: int = 5,
    include_raw_content: bool = False,
):
    """
    根据用户问题检索互联网公开信息

    注意：本工具只用于外部公开网页、新闻、政策等信息，不用于查询业务数据库或 RAGFlow 私有知识库
    :param query: 搜索关键词或自然语言问题
    :param topic: 搜索主题，可选 news、finance、general
    :param max_results: 返回的最大结果数
    :param include_raw_content: 是否返回网页原文内容；False 返回摘要，True 尝试返回更完整正文
    :return: Tavily 返回的结构化搜索结果
    """
    # 工具内部埋点比外层 stream 解析更直接：只要工具被调用，前端就能看到本次搜索参数
    # 这里只上报查询参数，不上报搜索结果正文，避免监控事件体过大
    monitor.report_tool(
        tool_name="网络搜索工具",
        args={
            "query": query,
            "topic": topic,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        },
    )

    # Tavily 返回 query、results、title、url、content 等结构化字段，后续由子智能体阅读并汇总
    return tavily_client.search(
        query=query,
        topic=topic,
        max_results=max_results,
        include_raw_content=include_raw_content,
    )


if __name__ == "__main__":
    from pprint import pprint

    # 本地调试入口：直接运行本文件可验证 TAVILY_API_KEY 和 Tavily API 是否可用
    pprint(
        internet_search.invoke(
            {"query": "2026中国法定节假日放假安排表，我天天都想要放假"}
        )
    )
```

### 4.1 参数说明

| 参数                  | 说明                                         |
| --------------------- | -------------------------------------------- |
| `query`               | 搜索关键词或搜索问题                         |
| `topic`               | 搜索主题，可选 `general`、`news`、`finance`  |
| `max_results`         | 最多返回多少条结果，本项目默认 5 条          |
| `include_raw_content` | 是否返回更完整的原始内容，默认只返回精简内容 |

对 Agent 来说，函数参数和函数说明都很重要。`@tool` 会把这些信息暴露给模型，模型会根据说明决定怎么填参数。

### 4.2 Tavily 返回结果长什么样

`internet_search` 返回的不是一句自然语言，而是 Tavily API 的结构化结果。

可以先把它理解成下面这种结构：

```json
{
  "query": "2026 年 AI 行业政策",
  "results": [
    {
      "title": "网页标题",
      "url": "https://example.com/article",
      "content": "搜索结果摘要或正文片段",
      "score": 0.91,
      "raw_content": "更完整的网页原文内容"
    }
  ]
}
```

其中最常用的是：

| 字段          | 作用                                                    |
| ------------- | ------------------------------------------------------- |
| `query`       | 本次真实提交给 Tavily 的搜索问题                        |
| `results`     | 搜索结果列表                                            |
| `title`       | 网页标题，帮助模型快速判断来源主题                      |
| `url`         | 原始网页地址，方便后续追溯来源                          |
| `content`     | Tavily 提取出的摘要内容，是模型主要阅读的信息           |
| `score`       | 搜索结果相关性分数，可用于判断结果是否贴近问题          |
| `raw_content` | 原始正文内容，只有打开 `include_raw_content` 时才更完整 |

这就是为什么本项目使用 Tavily，而不是让模型直接“想象网页内容”。工具返回的是可追溯的数据：模型可以阅读 `content`，必要时保留 `url`，主智能体后面整理报告时也能知道信息来自哪里。

学习阶段建议 `max_results` 保持 5，`include_raw_content` 先保持 `False`。等你发现摘要信息不够，再打开原文内容，否则返回文本太长，会增加子智能体阅读成本。

### 4.3 实际运行输出怎么读

在项目根目录运行：`uv run python -m app.tools.tavily_tool`

一次真实输出会先看到工具监控事件：

```text
[Monitor:tool_start] 开始执行工具: 网络搜索工具
```

这说明 `internet_search` 里的 `monitor.report_tool(...)` 已经生效：工具真正请求 Tavily 之前，先把“网络搜索工具开始执行”这件事汇报给监控模块。后面接着才是 Tavily 返回的搜索结果。

下面是把实际输出压缩后的结构，重点看字段，不需要把很长的网页正文都放进教程或报告里：

```python
{
    "answer": None,
    "follow_up_questions": None,
    "images": [],
    "query": "2026中国法定节假日放假安排表，我天天都想要放假",
    "request_id": "6005dc62-...",
    "response_time": 0.75,
    "results": [
        {
            "title": "国务院办公厅关于2026年部分节假日安排的通知",
            "url": "http://www.scio.gov.cn/zdgz/jj/202511/t20251110_938367.html",
            "content": "经国务院批准，现将2026年元旦、春节、清明节、劳动节、端午节、中秋节和国庆节放假调休日期的具体安排通知如下...",
            "score": 0.86981434,
            "raw_content": None,
        },
        {
            "title": "國務院辦公廳關於2026年部分節假日安排的通知 - 中國政府網",
            "url": "http://big5.www.gov.cn/gate/big5/www.gov.cn/gongbao/2025/issue_12406/202511/content_7048922.html",
            "content": "經國務院批准，現將2026年元旦、春節、清明節、勞動節、端午節、中秋節和國慶節放假調休日期的具體安排通知如下...",
            "score": 0.8215175,
            "raw_content": None,
        },
        "... 其余结果省略 ..."
    ],
}
```

这段输出里有几个很值得注意的点：

| 现象                                               | 说明                                                              |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| `answer` 是 `None`                                 | 当前调用主要拿搜索结果列表，不依赖 Tavily 直接生成最终答案        |
| `follow_up_questions` 是 `None`、`images` 是空列表 | 本次搜索没有返回追问建议和图片，这不是报错                        |
| `request_id` 有值                                  | 每次 Tavily 请求的追踪 ID，排查接口问题时有用                     |
| `response_time` 是 `0.75`                          | 本次请求大约 0.75 秒返回，可以粗略观察搜索耗时                    |
| `results` 返回 5 条                                | 对应工具默认的 `max_results=5`                                    |
| `raw_content` 是 `None`                            | 因为默认 `include_raw_content=False`，所以主要阅读 `content` 摘要 |
| `score` 从高到低变化                               | 可以辅助判断相关性，但不能替代来源判断                            |

还要特别注意：搜索结果不等于最终答案。上面这次搜索中，前两条是政府相关来源，后面也混入了旅游网站、便民查询站等页面。网络搜索助手在总结时，应该优先阅读标题、URL 和相关性分数都更可靠的结果；对于明显广告化、聚合站或主题偏离的结果，要降低权重，必要时换关键词继续搜索。

---

## 5、进度上报：monitor 与 stream

### 5.1 为什么工具里要调用 monitor

第 9 章已经写过 `monitor.py`。它的作用是把工具调用、子智能体调用和任务结果推给前端。

这里把埋点写在工具内部：

```python
monitor.report_tool(
    tool_name="网络搜索工具",
    args={
        "query": query,
        "topic": topic,
        "max_results": max_results,
        "include_raw_content": include_raw_content,
    },
)
```

只要 Agent 调用了 `internet_search`，前端就能看到“正在调用网络搜索工具”，并且能看到这次搜索的参数。

这一行代码先解决工具级进度。网络搜索助手是第一个子智能体，还没有进入完整的主智能体接口和前端联调阶段，所以先让工具自己汇报进度，链路最短，也最容易验证。

### 5.2 两种向前端推送进度的方式

这里要解决一个工程问题：Agent 执行过程可能比较长，前端不能一直等最终答案。后端需要在中间步骤里不断推送消息，例如：

```text
正在调用网络搜索助手
正在执行网络搜索工具
搜索参数是什么
任务执行完成
```

本项目里会同时遇到两类“流”：

```mermaid
flowchart TD
    Agent["DeepAgent 执行中"] --> Stream["stream/astream：给后端代码解析 chunk"]
    Agent --> Monitor["monitor.report_tool：主动上报业务事件"]
    Stream --> Parser["解析 model/tools/task_result"]
    Parser --> WS["WebSocket 推送给前端"]
    Monitor --> WS
    WS --> FE["前端进度面板"]
```

`stream/astream` 更偏框架运行状态，适合后端判断模型、工具和子智能体调用；`monitor` 更偏业务展示事件，适合把“正在搜索什么”这种人能看懂的消息推给前端。两者配合起来，页面既能看到 Agent 的真实执行过程，也能看到更友好的业务说明。

这个项目里，向前端推送进度大体有两种做法。

**方式一：在 stream 流式输出里统一解析**

DeepAgents 底层是图执行逻辑，所以主智能体可以用 `stream` / `astream` 流式执行。流式执行时，后端不是等整个任务结束，而是不断拿到一个个 `chunk`：

```text
主智能体开始执行
  -> stream 产出 chunk
  -> 后端判断这个 chunk 代表什么事件
  -> 如果是调用工具，就推送 tool 事件
  -> 如果是调用子智能体，就推送 assistant 事件
  -> 前端实时展示进度
```

可以先看一个简化版伪代码。这里的 `is_tool_call_chunk`、`is_sub_agent_chunk` 只是为了说明判断思路，不是本章要直接复制的真实函数：

```python
async for chunk in main_agent.astream(
    {"messages": [{"role": "user", "content": task_query}]},
    config=config,
    subgraphs=True,
):
    # 统一处理主智能体和子智能体执行过程中吐出来的片段
    if is_tool_call_chunk(chunk):
        monitor.report_tool(
            tool_name=get_tool_name(chunk),
            args=get_tool_args(chunk),
        )

    elif is_sub_agent_chunk(chunk):
        monitor.report_assistant(
            assistant_name=get_assistant_name(chunk),
            args=get_assistant_args(chunk),
        )
```

这种做法的好处是：**所有进度都在主执行循环里统一处理**。后续如果前端要做更完整的执行时间线，比如“主智能体 -> 子智能体 -> 工具 -> 返回结果”，流式解析会更集中。但它有一个容易踩坑的地方：如果只对主智能体做普通流式输出，默认更容易看到主智能体这一层的事件；子智能体内部又调用了哪些工具，不一定都会出现在主智能体的流式结果里。

所以如果希望把子智能体内部执行过程也拿出来，就要注意开启子图流式输出：

```python
subgraphs=True
```

可以把它理解成一句话：**子智能体也是一张子图，只有把子图也纳入流式输出，后端才更容易从 chunk 里观察到子智能体内部的工具调用过程。**

**方式二：在工具内部直接埋点**

第二种做法更直接：不等外层 stream 去解析，工具一被调用，就在工具函数内部主动上报。

本章采用的就是这种方式。它的逻辑很简单：

```text
Agent 调用 internet_search
  -> internet_search 内部先调用 monitor.report_tool
  -> monitor 根据当前 thread_id 找到对应前端连接
  -> WebSocket 把“正在执行网络搜索工具”推给前端
  -> 工具继续调用 Tavily，返回搜索结果
```

它的优点是稳定、直观，并且和 chunk 结构解耦。只要这个工具真的被调用了，它就会自己推送一条进度。

它的代价是：每个工具都要主动写一行类似的埋点代码。如果工具很多，就要保持统一规范，比如工具名怎么写、参数要不要脱敏、前端展示什么字段。

两种方式可以这样对比：

| 方案            | 核心做法                                         | 优点                             | 注意事项                                                       |
| --------------- | ------------------------------------------------ | -------------------------------- | -------------------------------------------------------------- |
| stream 流式解析 | 在主智能体 `stream` / `astream` 循环里解析 chunk | 统一入口，适合构建完整执行时间线 | 子智能体内部过程需要关注 `subgraphs=True`，还要解析 chunk 结构 |
| 工具内部埋点    | 在每个工具函数里调用 `monitor.report_tool(...)`  | 简单直接，工具被调用就能推送     | 每个工具都要写埋点，并保持事件格式一致                         |

本项目后续会两种方式都用到：调用子智能体这类“调度层事件”，更适合在主智能体流式执行过程中识别；具体工具被调用这类“工具层事件”，可以直接在工具内部埋点。本章先从 `internet_search` 开始做工具埋点，是为了让第一条前端进度链路先跑通。

---

## 6、组装 network_search_agent

工具写完以后，就可以把它和提示词配置组装成子智能体。

项目对应文件路径：`deepsearch-agents/app/agent/subagents/network_search_agent.py`

这个文件只做一件事：把 YAML 里的网络助手配置和 `internet_search` 工具组装成 DeepAgents 认识的字典。

```python
"""
网络搜索子智能体配置模块

将 app/prompt/prompts.yml 中的 tavily 配置与 internet_search 工具组装成
DeepAgents 可识别的字典式子智能体。主智能体后续会根据 description
决定是否把公开网络信息查询任务分派给它。
"""

from app.agent.prompts import sub_agents_content
from app.tools.tavily_tool import internet_search


# 字典式子智能体的核心字段来自 YAML，便于后续只改配置就能调整路由描述和行为约束
# tools 列表声明该子智能体可以调用的真实外部能力
network_search_agent = {
    "name": sub_agents_content["tavily"]["name"],
    "description": sub_agents_content["tavily"]["description"],
    "system_prompt": sub_agents_content["tavily"]["system_prompt"],
    "tools": [internet_search],
}
```

这里采用的是 DeepAgents 最常见的字典式子智能体写法。注意，`network_search_agent.py` 并没有把提示词硬编码在 Python 文件里，而是从 `app.agent.prompts` 中读取 `sub_agents_content`。在 `app/agent/prompts.py` 里，`sub_agents_content` 来自 `prompt_yaml_content["sub_agents"]`，也就是前面配置的 `prompts.yml`。这样后续只想调整助手描述或检索策略时，优先改 YAML 即可，不需要反复改 Python 代码。

| 字段            | 来源                       | 作用                         |
| --------------- | -------------------------- | ---------------------------- |
| `name`          | `prompts.yml`              | 子智能体名称                 |
| `description`   | `prompts.yml`              | 给主智能体判断何时调用       |
| `system_prompt` | `prompts.yml`              | 给网络搜索助手自己的行为约束 |
| `tools`         | `app/tools/tavily_tool.py` | 子智能体可以调用的真实工具   |

---

## 7、网络搜索助手的执行过程

网络搜索助手执行时，大致会经历下面的过程：

```mermaid
flowchart TD
    Start[接收主智能体分派的任务] --> Judge{是否需要公开网络信息}
    Judge -- 否 --> Return[说明不适合由网络助手处理]
    Judge -- 是 --> Rewrite[拆解搜索角度]
    Rewrite --> Search[调用 internet_search]
    Search --> Observe[阅读 Tavily 返回结果]
    Observe --> Enough{信息是否足够}
    Enough -- 否且未超过次数 --> Rewrite
    Enough -- 是或达到次数上限 --> Summary[整理搜索结果]
    Summary --> End[返回给主智能体]
```

这里要注意，网络搜索助手不是最终回答用户的角色。它只负责把外部资料查回来，然后把结果交给主智能体。最终怎么组织答案、是否生成 Markdown 或 PDF，是主智能体后续的工作。

---

**本章小结：**

本章完成了「深度研搜」项目的第一个子智能体：网络搜索助手。下一章会继续实现数据库查询助手。数据库助手比网络搜索助手多一个难点：它不是简单查一句话，而是要先看有哪些表，再看表结构和样例数据，最后才能让模型生成并执行 SQL。
