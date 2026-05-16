# 25 - LangGraph 高级特性

---

**本章课程目标：**

- 理解 LangGraph 的四类高级能力：**流式处理（Streaming）**、**状态持久化（Persistence）**、**时间回溯（Time-Travel）**、**子图（Subgraphs）**。
- 建立一个更工程化的认知：这些能力不是零散 API，而是 LangGraph 为真实生产场景提供的“可观测、可恢复、可复用、可扩展”的基础设施。
- 能运行并理解本章全部案例，知道这些高级特性分别解决什么问题、适合放在什么场景里使用。

**学习建议：** 本章建议按 **“先看流式 → 再看持久化 → 再看时间回溯 → 最后看子图”** 的顺序学习。因为在真实项目里，流式和持久化最常先落地，时间回溯更偏调试与恢复能力，子图则更偏结构拆分与复用。

**官方文档与资源**：详见 [工具导航与参考资料索引 - LangGraph](工具导航与参考资料索引.md#LangGraph)。

---

## 1、流式处理（Streaming）

### 1.1 定义

在很多人的印象里，“流式输出”常常只等于“大模型逐 token 打字机式输出”。但放到 LangGraph 里，流式处理的范围更大。它不仅能输出模型生成过程，还能把**图执行过程中的状态变化、节点进度、子图过程、自定义消息**一边执行一边暴露出来。

这也是 LangGraph 流式处理和普通模型流式输出最大的区别：

- **普通 LLM 流式**：更关注“模型文字怎么一点点吐出来”
- **LangGraph 流式**：更关注“整张图现在跑到哪一步了，状态发生了什么变化”

所以你可以先把 LangGraph Streaming 理解成：**把图执行过程拆开给你看，而不是等整张图完全跑完才给最终结果。**

### 1.2 为什么流式处理很重要

流式处理不是“锦上添花”的体验优化，而是很多 AI 应用的重要基础能力。真实项目里常见需求包括：

- 前端希望边执行边展示当前进度，而不是长时间白屏等待
- 调用大模型时，希望 token 级别实时显示
- 工作流较长时，希望知道当前执行到哪个节点
- 调试复杂图时，希望看到每一步到底更新了什么状态
- 子图或工具内部有重要中间结果，希望在最终结果出来前先看到过程

所以这一点有两层价值：**用户体验层**：更快感知结果正在生成；**工程调试层**：更容易观察图内部到底发生了什么。

### 1.3 stream() 和 invoke() 的区别

这一点非常值得先讲清楚：

- `invoke()`：等整张图跑完，再返回最终结果
- `stream()` / `astream()`：图在运行过程中，就把中间结果分批往外送

也就是说：

- 如果你只关心最后结果，用 `invoke()`
- 如果你想一边执行一边观察，用 `stream()` 或 `astream()`

LangGraph 图本身实现了 **Runnable** 接口，所以自然拥有这些流式能力。这也让它和 [LangChain `Runnable` / LCEL](15-LCEL与链式调用.md) 体系能够衔接起来。

不过这里还要多补一个关键点：`stream()` 不是只有一种固定输出格式。你在调用它时，通常还会配合一个很重要的参数：`stream_mode`。这个参数决定了“图在执行过程中，到底往外流什么”，比如是流完整状态、流增量更新、流模型消息片段，还是流自定义进度信息。

### 1.4 stream_mode 有哪些

LangGraph 通过 `stream_mode` 指定“到底想流什么”。

当前最常见、最值得你先掌握的模式有这些：

| 模式       | 含义                                  |
| ---------- | ------------------------------------- |
| `values`   | 每一步结束后输出当前完整状态快照      |
| `updates`  | 每一步结束后只输出本步的增量更新      |
| `messages` | 输出 LLM 生成过程中的消息片段 / token |
| `custom`   | 输出节点内部主动写出的自定义消息      |
| `debug`    | 输出更完整、更底层的调试信息          |

如果你想同时拿到多种流，可以直接传列表，例如：

```python
stream_mode=["updates", "custom"]
```

这时返回的流式结果通常会带上“当前是哪一种模式的数据”。

### 1.5 values 和 updates 怎么区分

这是本章里最容易混的一组概念。

- `values`：每一步都给你“当前完整 State 长什么样”
- `updates`：每一步只给你“这一小步到底改了哪些字段”

从调试体验上说：

- `values` 更像“每一步的全量快照”
- `updates` 更像“每一步的增量日志”

### 1.6 案例：流图状态（values / updates）

这个案例就是用最直接的方式，把 `values` 和 `updates` 的差别跑给你看。它的重点不是业务逻辑，而是让你建立一个流式观察状态变化的直觉。

【案例源码】`案例与源码-3-LangGraph框架/07-senior/streaming/StreamGraphState.py`

[StreamGraphState.py](案例与源码-3-LangGraph框架/07-senior/streaming/StreamGraphState.py ":include :type=code")

### 1.7 案例：多模式流与 debug

当你把 `stream_mode` 设成列表时，一次运行里就能同时拿到多种类型的流。这个案例最值得观察的是：

- 多种模式一起开时，输出长什么样
- `debug` 模式为什么更适合调试，而不是直接拿去做业务 UI

【案例源码】`案例与源码-3-LangGraph框架/07-senior/streaming/StreamMultipleModes.py`

[StreamMultipleModes.py](案例与源码-3-LangGraph框架/07-senior/streaming/StreamMultipleModes.py ":include :type=code")

### 1.8 案例：LLM 逐 token 流式输出（messages）

如果某个节点里调用了大模型，`messages` 模式就特别有价值。它可以帮助你在图运行过程中，直接拿到模型生成的消息片段，而不用等节点完全执行完。

这也是为什么 LangGraph Streaming 不只是“图状态流”，它还能把模型输出也纳入统一流式体系。

【案例源码】`案例与源码-3-LangGraph框架/07-senior/streaming/StreamLLMTokens.py`

[StreamLLMTokens.py](案例与源码-3-LangGraph框架/07-senior/streaming/StreamLLMTokens.py ":include :type=code")

### 1.9 案例：自定义数据流（custom）

有时候你想流的不是状态，也不是 token，而是业务自定义进度。例如：

- “正在检索知识库”
- “正在生成回答”
- “当前进度 60%”

这时就可以在节点内部通过流写入器主动写出自定义数据，然后用 `custom` 模式接收。

这两个案例的关系可以这样理解：

- `StreamCustomDataSimple.py`：先看最小可运行版本
- `StreamCustomData.py`：再看更贴近真实项目的进度与组合模式写法

【案例源码】`案例与源码-3-LangGraph框架/07-senior/streaming/StreamCustomDataSimple.py`

[StreamCustomDataSimple.py](案例与源码-3-LangGraph框架/07-senior/streaming/StreamCustomDataSimple.py ":include :type=code")

【案例源码】`案例与源码-3-LangGraph框架/07-senior/streaming/StreamCustomData.py`

[StreamCustomData.py](案例与源码-3-LangGraph框架/07-senior/streaming/StreamCustomData.py ":include :type=code")

### 1.10 小结：什么时候该用哪种流

你可以按下面这张小表来记：

| 需求                   | 更适合的模式 |
| ---------------------- | ------------ |
| 想看整张图当前完整状态 | `values`     |
| 想看每一步改了什么     | `updates`    |
| 想看 LLM token         | `messages`   |
| 想推送业务自定义进度   | `custom`     |
| 想详细调试图内部执行   | `debug`      |

---

## 2、状态持久化（Persistence）

### 2.1 定义

如果说流式处理解决的是“图在运行过程中怎么被看见”，那状态持久化解决的就是另一件很重要的事：**图跑到一半、跑完之后，状态能不能被记住，并在下次继续使用。**

LangGraph 的持久化核心围绕 **checkpoint（检查点）** 展开。官方文档的说法可以概括成一句话：**当你给图配置了 checkpointer，图在执行的每一步都可以把当前状态保存成一个检查点。** 被保存的字段与合并规则仍由你在 [第 23 章](23-LangGraphAPI：图与状态.md) 定义的 **State / Reducer** 决定。

这些检查点会被组织到某个 **thread** 下面。入门阶段，可以先把 thread 理解成“同一条会话或同一条工作流链路”的 ID 容器，而最常见的就是通过：

```python
{"configurable": {"thread_id": "..."}}
```

来区分不同对话、不同用户或不同执行线程。

![Checkpoint 持久化概念：自动存档、失败恢复、暂停与恢复、时间旅行与审计追踪（images/25/25-2-1-1.jpeg）](images/25/25-2-1-1.jpeg)

**图注：** 上图概括 **Checkpoint 在生产场景中的价值**（存档、容错、断点续跑、回溯与审计）；`thread_id` 则用于在存储侧把同一对话/任务链的检查点归并到一条「线程」下，与图中「按步落盘」互补。

### 2.2 为什么持久化很重要

LangGraph 的很多高级能力，其实都建立在持久化之上。官方文档里明确提到，持久化是这些能力的基础：

- 人工介入（human-in-the-loop）
- 对话 / 线程级记忆
- 时间回溯（time-travel）
- 容错恢复（fault-tolerant execution）

所以持久化不是“额外加的一层存储”，而是 LangGraph 为什么适合做生产级 Agent / Workflow 的关键原因之一。

### 2.3 短期记忆：Checkpointer

在 LangGraph 语境里，最常先接触到的是 **Checkpointer**。

这里说的 Checkpointer，本质上是：

- 按 `thread_id` 保存图的执行状态
- 让同一个线程下的多次调用可以继续沿用之前的状态

所以 Checkpointer 更像是：**线程内、会话内、工作流运行期的短期记忆。**

这和你前面学过“消息历史”“短期记忆”的主线，是能够串起来的。区别在于，这里不是单独记消息，而是记**整张图的状态快照**。

### 2.4 长期记忆：Store / BaseStore

只用 Checkpointer 还不够，因为它更偏“同一条线程内部的连续状态”。那如果我们想跨线程、跨会话保存长期信息呢？

这就轮到 **Store** 出场了。

官方 Persistence 文档里把它解释得很清楚：**Checkpointer 保存线程内状态，Store 用来保存跨线程共享的长期信息。**

所以两者最核心的区别可以这样记：

- **Checkpointer**：保存图在某条 thread 里的运行状态
- **Store / BaseStore**：保存跨 thread、跨会话仍然要长期保留的数据

例如：

- 用户偏好
- 长期业务事实
- 跨会话共享的知识片段

这些都更适合放 Store，而不是硬塞进单条 thread 的 checkpoint 链里。

### 2.5 持久化后端怎么选

从本地学习到真实部署，持久化后端通常会有一个很自然的演进路线：

- **内存**：最适合学习和临时验证
- **SQLite**：适合本地开发、小型项目、单机轻量部署
- **Postgres / Redis / 其他数据库后端**：更适合生产环境

官方文档里也把 checkpointer 实现拆成了不同安装包和后端类型。入门阶段不用一开始把所有后端都背下来，先知道下面这些即可：

- **先学概念**
- **再学内存和 SQLite**
- **生产再考虑 Postgres / Redis 等后端**

![持久化后端演进示意：内存 → SQLite → Postgres/Redis 等（动图）（images/25/25-2-5-1.gif）](images/25/25-2-5-1.gif)

**图注：** 学习阶段多用内存 Checkpointer；本地与小型部署常用 SQLite；生产环境再按可用性与运维需求选用 Postgres、Redis 等官方或社区后端实现。

### 2.6 案例：内存检查点（MemoryPersistence）

这个案例最适合先建立“checkpoint 到底是什么”的第一直觉。因为它不需要额外数据库配置，能让你专注观察：

- 同一条 thread 下状态是怎么延续的
- 为什么图执行完后，状态还能被后续调用接上

【案例源码】`案例与源码-3-LangGraph框架/07-senior/state_persistence/MemoryPersistence.py`

[MemoryPersistence.py](案例与源码-3-LangGraph框架/07-senior/state_persistence/MemoryPersistence.py ":include :type=code")

### 2.7 案例：SQLite 检查点（SqlitePersistence）

当你已经理解内存版 checkpoint，再看 SQLite 会更顺。这个案例更像是在回答：**如果我不想让状态只存在进程内，而想把它真正保存到本地数据库里，怎么做？**

它也很适合作为“从学习版走向更接近真实部署版”的过渡。

【案例源码】`案例与源码-3-LangGraph框架/07-senior/state_persistence/SqlitePersistence.py`

[SqlitePersistence.py](案例与源码-3-LangGraph框架/07-senior/state_persistence/SqlitePersistence.py ":include :type=code")

### 2.8 案例：预构建 Agent 与持久化（AgentPersistence）

这个案例很有价值，因为它把前面 LangChain Agent 那一条主线和 LangGraph 持久化真正连起来了。即使你用的是高层的 `create_agent`，底层依然能借助 LangGraph 的持久化能力，让同一 `thread_id` 下的多轮对话具有连续性。

这也能帮助读者建立一个更完整的认知：

- LangGraph 不只是“你手写图时才会用到”
- 它的持久化能力也会支撑更高层的 Agent 体系

【案例源码】`案例与源码-3-LangGraph框架/07-senior/state_persistence/AgentPersistence.py`

[AgentPersistence.py](案例与源码-3-LangGraph框架/07-senior/state_persistence/AgentPersistence.py ":include :type=code")

---

## 3、时间回溯（Time-Travel）

### 3.1 定义

时间回溯是 LangGraph 很有代表性、也很体现“生产级工作流”思路的一项能力。

它解决的问题不是“怎么正常跑一张图”，而是：**图已经跑过了，我能不能回到历史中的某一步，从那里重新继续跑，甚至改一改状态再跑。**

这类需求在普通线性脚本里很难优雅实现，但在 LangGraph 里，因为前面已经有了 checkpoint 链，所以时间回溯就变得自然了。

### 3.2 为什么时间回溯有价值

时间回溯最重要的价值，不是“炫技”，而是它特别适合处理**非确定性系统**，尤其是由 LLM 驱动的 Agent / Workflow。

真实项目里很常见的问题包括：这次为什么回答对了，我想回看中间过程；这次为什么跑偏了，我想定位到底在哪一步开始出问题；如果在某一步换一个状态、换一条分支，后面会发生什么。

所以时间回溯特别适合：调试、复盘、分支探索、人工修正后重跑。

### 3.3 时间回溯通常怎么做

把官方文档里的思路收敛成初学者更容易记的四步，大概就是：

1. 先跑一遍图，生成历史 checkpoint
2. 用 `get_state_history(...)` 找到你想回到的那个历史点
3. 视情况决定是原样恢复，还是先 `update_state(...)` 改状态
4. 再从那个历史点继续 `invoke(...)` 或 `stream(...)`

如果你把这四步理解成：

- 先有“历史录像”
- 再选“从哪一帧切回去”
- 可选“改一下剧本”
- 然后“从那里继续往后演”

就会非常好记。

### 3.4 案例：TimeTravel

这个案例的学习重点不是死记 API，而是看清楚：

- 历史 checkpoint 是怎么被拿出来的
- 目标 checkpoint 是怎么选的
- 修改状态后，为什么会形成新的执行分支

也就是说，时间回溯不是“抹掉过去”，而是**基于过去某个点，再分出一条新的未来路径。**

【案例源码】`案例与源码-3-LangGraph框架/07-senior/time_travel/TimeTravel.py`

[TimeTravel.py](案例与源码-3-LangGraph框架/07-senior/time_travel/TimeTravel.py ":include :type=code")

---

## 4、子图（Subgraphs）

### 4.1 定义

当图开始变复杂时，最自然的问题就是：**能不能把一整张图，当成另一张图里的一个节点来复用？**

这正是子图要解决的问题。LangGraph 里的子图，可以理解成：**把一个已经编译好的图，嵌入到另一张更大的父图里。**

所以子图的价值，本质上在于：复杂流程拆分、模块化复用、父子流程解耦。

![子图概念：父图中 Node_3 为 Sub_Graph，内含子流程；主图从 START→Node_1 分支至 Node_2 或子图，再汇聚至 END（子图内起点误写为 STAER，应理解为 START）](images/25/25-4-1-1.jpeg)

### 4.2 为什么需要子图

当流程越来越长时，如果所有节点都堆在一张图里，会出现几个问题：图结构越来越难读；某个局部流程没法单独测试；相似流程难复用；不同业务子模块之间耦合越来越重。

这时子图就很像“工作流层面的函数抽取”。

你可以把它和普通函数封装做一个类比：

- 普通函数：把一段 Python 逻辑封起来复用
- 子图：把一段 LangGraph 工作流封起来复用

### 4.3 子图最常见的三种理解方式

子图最容易从这三种模式入手理解：

1. **最简单模式**：把编译后的子图直接当成父图里的节点
2. **共享字段模式**：父图和子图共享部分状态字段
3. **状态转换模式**：父图状态和子图状态结构不同，需要代理节点做转换

这三种模式，正好也是本章三个子图案例的递进顺序。

### 4.4 案例：子图作为节点（SubGraphHello）

这是最基础的子图案例。它的重点非常单纯：

- 子图也可以像普通节点一样被挂进父图
- 当父图执行到这个“节点”时，本质上就是在执行一整张子图

【案例源码】`案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphHello.py`

[SubGraphHello.py](案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphHello.py ":include :type=code")

### 4.5 案例：父子图共享状态字段（SubGraphSimple）

当父图和子图共享部分字段时，理解重点就变成了：

- 哪些字段是共享的
- 哪些字段是子图内部私有的
- 父图最终能看到哪些结果

这个案例特别有价值，因为它帮助读者意识到：**子图不是完全孤立的小黑盒，它可以和父图共享部分状态空间。**

【案例源码】`案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphSimple.py`

[SubGraphSimple.py](案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphSimple.py ":include :type=code")

### 4.6 案例：代理节点与状态转换（SubGraphPro）

这是最贴近真实项目的一种子图用法。因为很多时候，父图和子图的状态结构根本不是一套：

- 父图关心用户请求和最终答案
- 子图关心分析输入、中间步骤、分析结果

这时就不能直接把子图粗暴塞进去，而更推荐用一个父图代理节点完成三件事：

1. 父状态 → 子图输入
2. 调用子图
3. 子图输出 → 父状态

这个模式非常重要，因为它是“跨图状态解耦”的关键。

【案例源码】`案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphPro.py`

[SubGraphPro.py](案例与源码-3-LangGraph框架/07-senior/subgraph/SubGraphPro.py ":include :type=code")

### 4.7 子图再往前走一步：和持久化、记忆的关系

官方最新的子图文档里，其实还补充了一个很有价值的认知：**子图不只是结构复用问题，它还会和持久化、线程级状态、命名空间隔离联系起来。**

对当前教程阶段来说，不需要在这一章里把这部分讲得太深，但可以先埋一个正确认知：

- 子图如果涉及持久化，会带来父图 / 子图状态边界问题
- 子图如果要有独立记忆，还要考虑 thread 级别与命名空间隔离
- 子图作为普通节点直接嵌入时，通常最容易理解，也最适合初学阶段

这一层你现在先有个概念就够了，真正复杂的多智能体 / 子图持久化协作，会在后续章节里再继续展开。

---

**章节思考题：**

1. `values` 和 `updates` 两种流式模式分别更适合什么观察目标？

   **答案：** `values` 更适合观察某一时刻完整 State 长什么样，便于看全貌；`updates` 更适合观察每一步到底更新了什么，便于看过程和定位变化来源。一个看快照，一个看增量。

2. Checkpointer 和 Store 为什么不是同一层持久化能力？

   **答案：** Checkpointer 保存的是线程执行过程中的状态快照，解决的是“断点恢复和回放”；Store 更像跨线程或长期共享的数据存储，解决的是“业务数据放在哪里”。一个偏执行状态，一个偏应用数据。

3. 为什么说 Time-Travel 的前提不是“有日志”，而是“有 checkpoint”？

   **答案：** 因为 Time-Travel 不是单靠日志文本回忆流程，而是要真正拿到某个时刻可恢复的状态快照，才能从那个点继续看、继续跑或安全重放。所以没有 checkpoint，通常就做不了真正意义上的时光回溯。

4. 如果你要做一个“可流式展示、可断点恢复、可回放调试”的复杂 Agent 系统，你会如何组合 Streaming、Persistence 和 Time-Travel？

   **答案：** 我会让前端订阅 streaming 做实时展示，用 checkpointer 保存线程关键节点状态支持中断恢复，再结合 time-travel 对异常线程做回放和调试。三者组合后，系统既能看见过程，也能在出问题时回到关键节点重新分析。

5. 当线上某个线程跑偏后，你会如何利用 checkpoint 历史去定位问题、复盘过程并安全重跑？

   **答案：** 我会先定位这个线程最近几个 checkpoint 的状态变化，找出是哪一步把状态带偏；然后结合对应输入、节点输出和历史快照复盘问题形成过程；确认修复策略后，再基于合适的 checkpoint 重新运行，而不是整条链盲目重来。

**本章小结：**

- **Streaming** 让你不必等图完全执行结束再拿结果，而是能边跑边观察状态、消息、进度与调试信息。
- **Persistence** 是 LangGraph 很核心的生产能力。Checkpointer 管线程内状态，Store 更适合跨线程长期信息。
- **Time-Travel** 建立在持久化之上，本质上是从历史 checkpoint 恢复或修改后重跑，非常适合调试、复盘和分支探索。
- **Subgraphs** 让复杂工作流可以模块化拆分和复用，是从“小图”走向“大系统”的关键一步。
- 学完本章后，你至少应该：能说清 `stream()` 和 `invoke()` 的区别，以及 `values / updates / messages / custom / debug` 几种流式模式分别在看什么；知道 **Checkpointer** 和 **Store** 的边界，理解“线程内短期状态”和“跨线程长期信息”不是同一层；明白 **Time-Travel 依赖持久化**，以及 **Subgraph** 不只是拆文件，而是结构复用和模块边界。

**建议下一步：** 建议先完整运行 `案例与源码-3-LangGraph框架/07-senior` 下的 Streaming、Persistence、TimeTravel、Subgraph 全部案例，再继续学习下一章的多智能体内容。这样你会对 LangGraph 为什么适合做复杂 Agent 系统，有一个更完整的工程化理解。
