# 12 - Ollama 本地部署与调用

---

**本章课程目标：**

- 理解 **Ollama** 是什么、解决什么问题，以及它在整套 LangChain / Agent 学习路线里的位置。
- 掌握 Ollama 的**安装、模型目录配置、常用命令、模型拉取与验证**，并建立“本地模型运行”这条完整思路。
- 学会使用 **LangChain** 里的 `ChatOllama` 调用本机 Ollama 服务，理解它与 [第 11 章 Model I/O 与模型接入](11-Model-I-O与模型接入.md) 中云端模型调用的异同。

**学习建议：** 本章建议按 **“Ollama 是什么 → 为什么要本地部署 → 安装与模型目录 → 常用命令 → 拉取并验证模型 → LangChain 对接”** 的顺序学习。不要一上来就只记命令，而是先搞懂 Ollama 在整个 AI 应用开发中扮演什么角色。需要说明的是：**本章以 Ollama 官方文档、LangChain 官方 ChatOllama 集成文档和本项目当前案例为主线**，帮助你从“本地跑模型”顺利过渡到“在代码里调用本地模型”。

---

## 1、Ollama 简介

### 1.1 定义

**Ollama** 是一个用于**在本地运行开源大模型**的工具。你可以把它理解成：**帮你把模型下载、管理、加载、运行、暴露 API 这几件事封装起来的本地大模型运行环境。**

一句话总结：

> **Ollama = 让你用很少的命令，在自己电脑上把开源大模型跑起来。**

安装好之后，你通常只需要像下面这样输入一条命令：

```bash
ollama run qwen:4b
```

如果本地还没有这个模型，Ollama 会先下载；下载完成后，它会直接启动并进入交互模式。从初学者视角看，这比自己去处理模型权重、推理框架、启动服务、配置推理端口，要简单得多。

![Ollama 官方标志：羊驼线稿风格图标（品牌识别，常见于安装包与文档）](images/12/12-1-1-1.png)

**官方文档与资源：**

- **Ollama 官网**：https://ollama.com （入口与文档导航）
- **安装包下载**：https://ollama.com/download
- **模型搜索 / 模型库**：https://ollama.com/search
- **源码仓库（GitHub）**：https://github.com/ollama/ollama
- **Ollama 官方文档**：
  - https://ollama.com/docs （英文）
  - https://ollama.com/zh-CN/docs （中文）
- **LangChain 与 Ollama 集成文档**：
  - https://docs.langchain.com/oss/python/integrations/chat/ollama （英文）
  - https://docs.langchain.org.cn/oss/python/integrations/chat/ollama （中文）

### 1.2 Ollama 解决了什么问题

如果你已经学过前两章的云端模型调用，应该已经知道：通过阿里百炼、DeepSeek、OpenAI 这类平台调用模型，优点是简单、稳定、开箱即用；但它也有明显局限：

- 需要联网
- 需要 API Key
- 会产生调用费用
- 某些场景下，数据不能离开本地机器或企业内网

Ollama 对应的，正好是另一条路：**把模型放到你自己的电脑上跑。**

因此它最直接解决的是：

- **想离线使用模型**
- **想减少对云端 API 的依赖**
- **想做本地开发、本地测试**
- **想让敏感数据尽量不出本机**
- **想学习开源模型和本地推理的基本流程**

你可以把它和云端 API 调用理解成两种“模型接入方式”：

- **云端 API**：模型在别人服务器上，你通过网络调用
- **Ollama 本地运行**：模型在你机器上，你通过本机服务调用

### 1.3 Ollama 和云端 API 的区别

这部分一定要讲清楚，因为很多同学学 Ollama 时会下意识地把它当成“另一个模型平台”，其实它更像是**本地运行层**。

| 维度                 | 云端 API（如阿里百炼、DeepSeek）     | Ollama                                                    |
| -------------------- | ------------------------------------ | --------------------------------------------------------- |
| **模型在哪**         | 厂商服务器上                         | 你自己的电脑上                                            |
| **是否需要 API Key** | 通常需要                             | 本地运行通常不需要                                        |
| **是否依赖联网**     | 是                                   | 本地调用可不依赖外网，但首次拉模型一般需要联网            |
| **成本**             | 按调用计费                           | 模型本地推理不按 token 计费，但会消耗本机算力、内存、磁盘 |
| **适合什么**         | 快速接入、稳定服务、无需本地硬件负担 | 本地开发、隐私敏感场景、离线测试、学习开源模型            |

从真实项目角度看，这两者不是非此即彼，而是经常配合使用：

- 本地开发阶段，用 Ollama 跑小模型验证逻辑
- 上线阶段，再切换到更强、更稳定的云端模型
- 或者企业内网环境中，本地 / 私有化模型与云端模型混合使用

### 1.4 使用场景

从项目角度给一个比较稳的建议：

- **本地开发 / 课程练习**：非常适合用 Ollama
- **企业内网原型 / 隐私敏感验证**：也很适合
- **对性能、稳定性、并发要求很高的正式推理服务**：要根据业务再评估是否继续用 Ollama，还是切向更专业的推理部署方案

但也要有合理预期：

- 它不等于“任何模型都能在你的电脑上丝滑跑起来”
- 它也不等于“本地跑一定比云端便宜或更强”
- 它更像一个**本地推理入口**，适合开发、实验、教学和一些轻中量应用

### 1.5 优势与局限

学习时，最好同时看到它的优点和边界。

**优势：**

- 安装和使用门槛低
- 命令简单，适合初学者
- 模型管理方便，`pull / run / list / rm` 一套命令就够用
- 本地调用通常不需要 API Key
- 与 LangChain 的 `ChatOllama` 集成成熟

**局限：**

- 是否跑得动，强烈依赖你的机器配置
- 模型体积大，会占内存和磁盘
- 本地模型能力通常取决于你能跑多大的模型
- 高并发、企业级推理服务场景，不一定优先选 Ollama

所以，对这章最准确的定位应该是：

> **Ollama 很适合学习本地模型、开发调试和轻量本地服务，但不是所有生产场景的唯一方案。**

---

## 2、安装与配置

### 2.1 安装前先知道两件事

在真正安装之前，初学者最容易忽略两件事：

1. **Ollama 程序本身不大，真正占空间的是模型**
2. **你未来可能会下载多个模型，因此模型目录最好一开始就想清楚**

这也是为什么很多教程安装完很快就会讲 `OLLAMA_MODELS`。  
因为模型文件一旦大起来，很容易把系统盘吃满。

### 2.2 下载方式

你可以从 Ollama 官网下载对应平台版本：

- **下载总入口**：https://ollama.com/download
- **Windows 下载页**：https://ollama.com/download/windows
- **macOS 下载页**：https://ollama.com/download/mac
- **Linux 下载页**：https://ollama.com/download/linux

Linux 下载页也提供非常常见的一键安装方式：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Windows 和 macOS 则更常见的是图形安装包。  
另外，LangChain 官方 ChatOllama 文档还提到：

- macOS 用户也可以通过 Homebrew 安装：`brew install ollama`
- 并通过 `brew services start ollama` 启动服务

所以从安装形式上，你可以先这样理解：

- **Windows**：安装包最常见
- **macOS**：安装包或 Homebrew
- **Linux**：安装脚本 / 手动安装 / systemd 服务

### 2.3 运行环境与硬件预期

这一节一定要说清楚，因为“能不能运行”不只是软件安装问题，更是硬件问题。

Ollama 跑得是否顺畅，主要受三件事影响：

- **模型大小**
- **系统内存 / 显存**
- **是否有可用 GPU 加速**

你可以先记一个粗略但实用的结论：

- **模型越大，占用的内存 / 显存越高**
- **小模型更适合本地学习**
- **不是所有电脑都适合一上来就跑 14B、32B、70B 级模型**

从经验上看，初学者更适合先从体量较小的模型开始，例如：

- `qwen:4b`
- 类似 7B / 8B 量级模型

而不是一开始就追求更大的模型。这也是为什么本项目案例里使用了更适合本地体验的标签，例如 `qwen:4b`。

**1）内存（RAM）**

参数越多，通常越吃内存。常见量级可粗记为：

- **约 7B（70 亿参数）**：建议至少 **8GB 可用内存**再跑 7B 级别模型（系统与其它软件还会占一部分，留余量更稳）。
- **约 13B**：建议约 **16GB** 内存级别。
- **约 33B**：建议约 **32GB** 内存级别。

若内存不够，容易出现加载失败、极慢或频繁换页卡顿。

**2）磁盘空间**

模型文件体积往往不小，除程序本体外，建议整体为 Ollama 与模型**至少预留约 50GB** 可用空间（多装几个模型时还要再加）。

**3）CPU**

性能较好、**多核**的 CPU 更有利于推理与并行，在纯 CPU 跑模型时体验差异会更明显。

**4）显卡（GPU）**

Ollama **可以只用 CPU 跑**。在 **NVIDIA GPU** 且驱动/CUDA 环境正常时，通常会走 GPU 加速，速度一般明显好于纯 CPU；在 **Apple Silicon（M 系列）** 上，Ollama 通常会利用 **Metal** 做加速，同样不必手动配置训练框架。具体是否走加速、占用哪块设备，以本机运行日志与活动监视器为准。

### 2.4 自定义安装路径与模型目录

如果你希望把 Ollama 或模型文件安装到非默认路径，例如 D 盘、大容量盘或专门的数据盘，那么建议尽早规划模型目录。

**Windows 下尤其建议不要把大模型长期堆在系统盘。**

你可以先准备一个目录，例如：

```text
D:\devSoft\Ollama\models
```

然后再通过环境变量或图形设置告诉 Ollama：以后模型存这里。

<img src="images/12/12-2-4-1.gif" alt="Windows 安装向导中自定义 Ollama 程序安装路径的操作步骤（动图）"/>

### 2.5 修改模型存储目录

如果你想把模型存到默认目录之外，可以设置环境变量：

- **变量名**：`OLLAMA_MODELS`
- **变量值**：你希望存放模型的目录路径

例如：

```text
OLLAMA_MODELS=D:\devSoft\Ollama\models
```

<img src="images/12/12-2-5-1.jpeg" alt="Windows「环境变量」对话框中新建用户变量 OLLAMA_MODELS 并指向自定义 models 目录"/>

根据 Ollama 官方 FAQ，默认模型目录通常是：

- **macOS**：`~/.ollama/models`
- **Linux**：`/usr/share/ollama/.ollama/models`
- **Windows**：`C:\Users\%username%\.ollama\models`

如果你要改路径，官方同样建议用 `OLLAMA_MODELS`。另外要注意：

- **Windows**：Ollama 会继承系统 / 用户环境变量
- **Linux（标准安装）**：如果使用 systemd 服务，通常要通过 systemd 配置环境变量
- **macOS（应用形式运行）**：官方 FAQ 推荐使用 `launchctl setenv`

这些平台差异在 Ollama 官方 FAQ 中都有说明：

- https://docs.ollama.com/faq

### 2.6 迁移或复用已有模型目录

如果你之前已经在其他目录下载过模型，可以直接把已有模型目录迁移过去，避免重复下载。

<img src="images/12/12-2-6-1.jpeg" alt="将已有 blobs、manifests 等模型目录内容复制到 OLLAMA_MODELS 指定路径以复用下载"/>

这在实际开发里非常有用，比如：

- 换电脑盘符
- 重装系统后恢复模型
- 在多个课程目录之间复用同一批模型

### 2.7 图形界面修改模型目录

部分 Ollama 桌面应用版本支持通过设置界面修改模型存储位置。如果你使用的是桌面客户端，可以在设置中查看是否存在 **Model location** 或类似选项。

<img src="images/12/12-2-7-1.png" alt="Ollama 桌面客户端菜单中打开 Settings（设置）的入口位置"/>

<img src="images/12/12-2-7-2.png" alt="在 Settings 中将 Model location 改为课程资料或自定义的 models 文件夹"/>

改完后，建议：

1. 重启 Ollama
2. 新开终端
3. 运行 `ollama list` 确认模型是否被正确识别

### 2.8 各平台环境变量设置差异

这部分对初学者很重要，因为很多“明明改了路径但不生效”的问题，本质上就是环境变量设置方式不对。

根据 Ollama 官方 FAQ：

**Windows：**

1. 先退出 Ollama
2. 打开系统环境变量设置
3. 为用户或系统创建 / 修改 `OLLAMA_MODELS`
4. 保存后重新启动 Ollama

**macOS：**

如果 Ollama 以应用形式运行，官方更推荐通过 `launchctl` 设置，例如：

```bash
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
```

同理，`OLLAMA_MODELS` 也可用相同方式设置，然后重启应用。

**Linux：**

如果 Ollama 以 systemd 服务运行，官方 FAQ 建议使用：

```bash
systemctl edit ollama.service
```

然后在 `[Service]` 下为每个变量增加一行，例如 `Environment="OLLAMA_MODELS=/path/to/models"`（可多条 `Environment=`），最后执行：

```bash
systemctl daemon-reload
systemctl restart ollama
```

所以你可以记住一个实用结论：

> **Windows 改系统环境变量，macOS 应用模式常用 `launchctl`，Linux 服务模式常用 `systemd`。**

---

## 3、常用命令

### 3.1 最常用的一组命令

安装完成后，你最常用到的其实就下面这些命令：

| 命令                                  | 说明                          |
| ------------------------------------- | ----------------------------- |
| `ollama pull llama3`                  | 下载指定模型                  |
| `ollama run llama3`                   | 运行模型并进入交互对话        |
| `ollama list`                         | 查看本机已下载模型            |
| `ollama rm llama3`                    | 删除模型                      |
| `ollama show llama3`                  | 查看模型详情                  |
| `ollama ps`                           | 查看当前加载中的模型          |
| `ollama stop llama3`                  | 停止正在运行的模型            |
| `ollama serve`                        | 启动 Ollama 本地服务          |
| `ollama create my-model -f Modelfile` | 基于 Modelfile 创建自定义模型 |

**退出 `ollama run` 交互对话**

用 `ollama run <模型名>` 进入聊天后，若要回到普通终端提示符：

- 在对话里输入 `/bye`（Ollama 提供的退出指令）；
- 或使用快捷键 **Ctrl+D**（向终端发送「结束输入」，在 macOS / Linux 上很常见；Windows 新终端多也支持，若无效可再试 **Ctrl+Z** 后回车，或直接关闭该终端标签页）。

### 3.2 ollama ps 命令说明

这条命令在真实项目里非常实用，因为它不只是告诉你“模型有没有运行”，还经常能帮助你判断：

- 模型是否真的加载了
- 是在 CPU 还是 GPU 上运行
- 当前有哪些模型驻留在内存中

Ollama 官方 FAQ 里也明确提到，`ollama ps` 可以帮助你看模型是否加载到了 GPU：

- `100% GPU`
- `100% CPU`
- 或 CPU / GPU 混合比例

这对排查“为什么本地这么慢”特别有帮助。

### 3.3 create 和 Modelfile 是什么

这属于进阶知识，但建议你先知道。Ollama 支持通过 **Modelfile** 创建自定义模型。你可以把 Modelfile 理解为：

> **Ollama 中“如何基于一个已有模型，定义系统提示、参数、模板等规则”的配置蓝图。**

官方文档：

- **Modelfile Reference**：https://docs.ollama.com/modelfile

本章不会展开自定义模型构建细节，但你至少要知道：`ollama create my-model -f Modelfile` **不是**重新训练模型，而更像是**基于已有模型做运行时封装**（系统提示、参数、模板等）。

---

## 4、安装与验证模型

### 4.1 验证 Ollama 是否安装成功

建议安装完成后，先做两个最基础的验证：1. 命令是否可用；2. 本地服务是否真的在监听

#### 4.1.1 看版本号

在终端执行：

```bash
ollama --version
```

如果命令可用，会输出类似：

```text
ollama version is 0.x.x
```

这至少说明两件事：

- Ollama 已经安装
- 终端里能找到 `ollama` 命令

#### 4.1.2 看默认端口是否监听

Ollama 本地 API 默认端口是 **11434**。  
如果服务正常启动，通常会在这个端口监听。

Windows 下常见验证方式：

```bash
netstat -ano | findstr 11434
```

如果看到类似：

```text
TCP    127.0.0.1:11434        0.0.0.0:0              LISTENING
```

说明 Ollama 服务已经在本机监听。

根据 Ollama 官方 API 文档，本地 API 默认地址是：

```text
http://localhost:11434/api
```

但要注意一点：

- **直接调 Ollama 原生 API** 时，通常会看到 `/api/...`
- **LangChain 的 `ChatOllama`** 一般只需要写根地址，例如 `http://localhost:11434`

这个区别很关键，后面写 LangChain 代码时会再次用到。

默认情况下，Ollama 只监听 **127.0.0.1**（本机回环）。若需要局域网内其他设备访问本机 Ollama，需在启动前通过环境变量 **OLLAMA_HOST** 绑定地址（如 `0.0.0.0:11434`），具体写法见 [Ollama FAQ](https://docs.ollama.com/faq) 中 “How do I configure Ollama server?” 一节。

### 4.2 模型从哪里找

如果你想知道 Ollama 里有哪些模型，最直接的方式是去官方模型库：

- **模型搜索 / 模型库**：https://ollama.com/search

这里你可以看到：

- 模型名称
- 标签（tag）
- 参数规模
- 是否支持 vision / tools / thinking 等特性

这一点非常重要，因为 Ollama 的模型名和标签必须写对。  
比如：

- `qwen:4b`
- `qwen3:8b`
- `deepseek-r1:14b`

这些标签都是“模型名 + 规格”。

### 4.3 以通义千问为例运行模型

执行 `ollama run <模型名>` 时，**若本地还没有该模型，Ollama 会先自动拉取（pull）再启动对话**，无需先单独执行 `ollama pull`；若已拉取过则直接进入交互模式。下载完成后会进入交互式对话。

常见示例命令：

```bash
ollama run qwen:4b
ollama run qwen3:8b
```

这里要提醒一句：

> **模型标签是否可用，要以当时官网模型库里的实际名称为准。**

不要死记教程里某个标签，最好学会自己去模型库里查。

### 4.4 使用课程资料中的离线模型

如果课程资料或你自己的磁盘里已经有现成的 `models` 目录，也可以直接通过：

- `OLLAMA_MODELS`
- 或图形界面里的 **Model location**

把 Ollama 指向那个目录，再执行：

```bash
ollama list
```

这样往往可以避免重复下载。

### 4.5 如何判断模型有没有真的跑起来

从学习和排障角度，最常用的判断方式有三种：

1. `ollama run <模型名>` 能正常进入对话
2. `ollama list` 能看到模型已下载
3. `ollama ps` 能看到模型正在内存中

对于初学者来说，这三条基本足够。

---

## 5、LangChain 整合 Ollama

### 5.1 为什么学会 Ollama 命令后，还要学 LangChain 接入

因为只会在终端里 `ollama run`，还不等于能把它接到自己的项目中。

真正的开发目标通常是：

- 在 Python 代码里调用本地模型
- 让本地模型也能接 Prompt、Parser、LCEL、Agent
- 让本地模型和云端模型一样，进入统一的 LangChain 生态

这也是本节的核心目的：

> **把 Ollama 从“命令行能聊天的工具”升级成“项目里能调用的模型端点”。**

### 5.2 ChatOllama 是什么

`ChatOllama` 是 LangChain 中用于连接本地 Ollama 聊天模型的类。你可以把它理解成：

> **本地模型版本的 Chat Model 客户端。**

这意味着，它在使用体验上会和你前面学过的：

- `ChatOpenAI`
- `init_chat_model(...)`

有很多共通点：

- 都可以 `invoke()`
- 都会返回 `AIMessage`
- 都能继续接 Prompt、LCEL、Agent

区别只在于：

- 前面那些大多连接的是云端模型
- `ChatOllama` 连接的是本机 Ollama 服务

### 5.3 最小用法：直接传字符串

最简单的写法可以这样：

```python
from langchain_ollama import ChatOllama

model = ChatOllama(
    model="qwen:4b",
    base_url="http://localhost:11434",
)

print(model.invoke("什么是 LangChain，100 字以内").content)
```

这和你在前面章节里学的“字符串 `invoke()`”几乎是一样的，只是端点从云端换成了本地。

### 5.4 消息列表写法：更贴近后续章节

如果你希望和 [第 13 章 提示词与消息模板](13-提示词与消息模板.md) 保持一致，也可以传消息列表：

```python
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

ollama_llm = ChatOllama(model="qwen3:8b")
messages = [HumanMessage(content="你好，请介绍一下你自己")]
resp = ollama_llm.invoke(messages)
print(resp.content)
```

这种写法的价值在于：  
后面你学 Prompt、Messages、多轮历史、Agent 时，思路是连续的。

### 5.5 显式写 base_url 原因

很多人会好奇：为什么有时代码里写 `base_url="http://localhost:11434"`，有时不写？

可以这样理解：

- **不写**：默认走本机默认地址
- **写了**：更显式、更清楚，也方便你以后切到远程 Ollama 或不同端口

比如：

```python
ChatOllama(
    model="qwen3:8b",
    base_url="http://localhost:11434",
)
```

这在教学上也更直观，因为你能明确知道自己连的是哪个服务地址。

### 5.6 基本案例

【案例源码】`案例与源码-2-LangChain框架/03-ollama/LangChain_Ollama.py`

[LangChain_Ollama.py](案例与源码-2-LangChain框架/03-ollama/LangChain_Ollama.py ":include :type=code")

这个案例是本章最核心的代码落地点。  
它对应的是：

- 使用 `ChatOllama`
- 指向本机 `http://localhost:11434`
- 直接 `invoke()` 一个问题
- 观察返回结果

虽然它很短，但意义很大，因为它完成了下面这件事：

> **把 Ollama 从“终端中的本地模型”变成“LangChain 代码中的模型对象”。**

---

**章节思考题：**

1. Ollama 和云端 API 在“模型运行位置”与“数据流向”上最核心的区别是什么？

   **答案：** Ollama 是把模型拉到本地机器运行，请求和数据主要在本机流转；云端 API 是把请求发到远端模型服务，数据和推理都发生在云端。前者更可控，后者更省本机资源。

2. `ollama pull`、`ollama run`、`ollama ps` 分别解决什么问题？

   **答案：** `ollama pull` 用来下载模型，`ollama run` 用来直接启动并交互测试模型，`ollama ps` 用来查看当前有哪些模型实例在运行。它们分别对应准备、试跑和查看状态三个阶段。

3. 为什么学会 Ollama 命令后，仍然要继续学习 `ChatOllama` 和 LangChain 接入？

   **答案：** 因为会命令只能说明你把模型跑起来了，不代表你已经能把它接进真实应用。继续学 `ChatOllama` 和 LangChain，才能把本地模型纳入统一编排、Prompt、Parser、RAG、Tool 等工程链路里。

4. 结合你的设备和项目需求，什么情况下你会优先选择本地 Ollama，而不是云端模型服务？

   **答案：** 当数据敏感、网络受限、需要离线使用、预算更适合本地算力，或者只是想快速做本地实验时，我会优先选 Ollama。若追求更强模型效果、部署更省心或团队硬件不足，则更适合选云端服务。

5. 如果本地模型出现“回答一般、速度偏慢、占用很高”这类问题，你会按什么顺序做诊断和优化？

   **答案：** 我会先判断是不是模型选型过大或机器资源不匹配，再看提示词和任务是否超出本地模型能力，接着检查并发、上下文长度和量化版本，最后再决定是换更轻模型、加硬件，还是改用云端服务。

**本章小结：**

- **Ollama** 是一个本地开源大模型运行环境，核心价值是让你可以在自己的电脑上下载、管理、运行模型，并通过本地 API 对外提供服务。它和前两章中的云端 API 调用不是替代关系，而是另一条“模型接入路线”：**云端模型在别人服务器上，本地模型在你自己机器上。**
- 本章最重要的实践线有两条：第一条是 **安装与模型管理**，包括下载 Ollama、规划模型目录、理解 `OLLAMA_MODELS`、掌握 `pull / run / list / rm / ps` 等常用命令；第二条是 **LangChain 接入**，也就是用 `ChatOllama` 把本地模型纳入和云端模型一致的编程方式中，继续使用 `invoke()`、消息列表和 `AIMessage` 这套统一抽象。
- 对初学者来说，最应该带走的不是死记所有命令，而是建立一个完整认知：**Ollama 负责把模型跑在本地，LangChain 负责把本地模型接进代码和应用流程里。** 学会这件事之后，后面的 Prompt、LCEL、Agent、RAG 都可以继续在本地模型上练习。
- 从掌握结果看，学完本章后，你至少应该：明白 **Ollama 是本地模型运行层**，它解决的是“模型怎么在本机跑起来”，不是替代 LangChain 的应用编排层；掌握最常用的模型管理动作：安装、拉取、运行、查看、删除、确认端口与模型目录；能用 `ChatOllama` 把本地模型接回 LangChain 的统一调用体系里，继续配合 Prompt、LCEL、Agent 使用。

**建议下一步：** 先亲手完成这条最小链路：安装 Ollama → `ollama run qwen:4b` 跑通一次本地模型 → 用 [LangChain_Ollama.py](案例与源码-2-LangChain框架/03-ollama/LangChain_Ollama.py) 在 Python 里调通本机模型。跑通之后，再进入 [第 13 章 提示词与消息模板](13-提示词与消息模板.md)、[第 14 章 输出解析器](14-输出解析器.md)、[第 15 章 LCEL 与链式调用](15-LCEL与链式调用.md)，把本地模型也串进完整的 LangChain 工作流里。
