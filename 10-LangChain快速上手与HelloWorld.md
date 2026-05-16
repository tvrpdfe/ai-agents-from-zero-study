# 10 - LangChain 快速上手与 HelloWorld

---

**本章课程目标：**

- 从“知道 LangChain 是什么”真正走到“**亲手跑通第一次 LangChain 调用**”，完成从环境准备到 HelloWorld 的闭环。
- 理解接入大模型最重要的 **调用三件套**：**API Key、模型名、Base URL**，并掌握 LangChain **0.x / 1.x** 两种基础写法。
- 会运行并理解本章全部案例：**环境检查、HelloWorld、多模型共存、企业级封装、流式输出**，为后续 [Model I/O](11-Model-I-O与模型接入.md)、[Ollama 本地调用](12-Ollama本地部署与调用.md)、[提示词与消息模板](13-提示词与消息模板.md)、[输出解析器](14-输出解析器.md) 打基础。

**学习建议：** 本章建议按 **“HelloWorld 是什么 → 环境与依赖 → 调用三件套 → 第一个案例 → 多模型共存 → 工程化写法”** 的顺序学习。不要一上来就记太多 API，先把第一次调用跑通，再理解它为什么这样写。需要说明的是：**LangChain 官方主线已经进入 1.x 时代**，因此本章以 **1.x 官方文档和当前项目依赖**为主，同时保留课程中仍然需要认识的 0.x / 经典写法，帮助你读懂旧资料与旧代码。

**官方文档与资源**：详见 [工具导航与参考资料索引 - LangChain](工具导航与参考资料索引.md#_LangChain)。

---

## 1、LangChain 环境与约定

### 1.1 支持的大模型与课程选用

LangChain 可以通过不同集成包接入很多模型提供商，官方提供了完整的 Provider 列表：

- **Providers Overview**：https://docs.langchain.com/oss/python/integrations/providers/overview

![LangChain支持的大模型](images/10/10-1-1-1.png)

本课程的选型是：

- **主线模型**：阿里云百炼 / 通义千问
- **辅助模型**：DeepSeek
- **扩展平台**：OpenRouter、硅基流动、Ollama 等

这样安排有两个现实原因：

1. **对国内开发者更友好**：注册、获取 API Key、访问稳定性、成本控制通常都更容易。
2. **便于迁移理解**：无论是百炼、DeepSeek，还是其他兼容 OpenAI 协议的平台，本质上都绕不开 **API Key、模型名、Base URL** 这套调用逻辑。

也就是说，本章虽然主要用 **阿里百炼 + DeepSeek** 举例，但你真正要学会的是“**怎么用 LangChain 接模型**”，而不是只会某一个平台。

### 1.2 Python 版本与项目环境约定

这一点一定要先说明清楚，因为它直接决定你后面会不会遇到一堆莫名其妙的兼容性问题。

根据 **LangChain 1.x 官方安装文档**和本项目当前依赖约定，建议你使用：

- **推荐版本**：Python **3.10**
- **支持范围**：Python **3.10–3.13**
- **不建议使用**：Python **3.14**

本仓库根目录的 [requirements.txt](requirements.txt) 已明确写明：项目当前推荐 **Python 3.10**，并说明 **`langchain-redis` 等依赖暂未兼容 3.14**。因此，本章不再沿用旧资料里常见的“Python 3.8+”说法，而是建议你直接按本项目约定来，后续章节更省心。

如果你是第一次跑本仓库案例，推荐做法是：

1. 在项目根目录创建虚拟环境
2. 激活虚拟环境
3. 安装本项目完整依赖

更细的环境准备步骤，可配合 [新手入门与常见问题](新手入门与常见问题.md) 一起看。

### 1.3 运行案例前置注意事项

这一节非常重要，很多人第一次跑不通不是代码问题，而是这两个约定没注意到。

**约定一：尽量在项目根目录运行案例。**  
本仓库很多脚本通过 `load_dotenv()` 从当前工作目录读取 `.env`。如果你在案例子目录里直接运行脚本，可能会读不到根目录下的 `.env`，从而出现 API Key 为空、401、403 等报错。

推荐写法：

```bash
python 案例与源码-2-LangChain框架/01-helloworld/LangChainV1.0.py
```

**约定二：先配置 `.env`，不要把 API Key 写死在代码里。**  
项目根目录提供了 `.env-example`，你可以复制一份改名为 `.env`，然后填入真实 Key。这样既安全，也方便切换环境。

---

## 2、常见大模型服务平台介绍

### 2.1 什么是调用三件套

无论你最终接的是阿里百炼、DeepSeek、OpenAI，还是其他兼容 OpenAI 协议的平台，绝大多数场景都绕不开三项信息：

- **API Key**：你是谁，用来鉴权
- **模型名**：你要调哪个模型
- **Base URL**：请求要发到哪里

这三项我把它简称为“**调用三件套**”。

可以把它们看作“打电话”时必须知道的三件事：

- **API Key**：相当于你的身份凭证
- **模型名**：相当于你要找哪位专家
- **Base URL**：相当于你拨打哪个号码

没有 API Key，平台不知道你是谁；没有模型名，平台不知道你要调哪个模型；没有 Base URL，请求甚至不知道该发往哪里。所以，本章后面的 HelloWorld 就是围绕这三件套展开。

### 2.2 常见平台一览

下面列出当前学习中比较常见的平台。你不需要一开始全部注册，但至少要知道它们的角色：

| 平台           | 入口                                                   | API Key 管理                                                        | 文档                                                                              | 模型                                                                         | 说明                                               |
| -------------- | ------------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------- |
| **阿里云百炼** | [平台](https://bailian.console.aliyun.com/)            | [API-Key](https://bailian.console.aliyun.com/?tab=model#/api-key)   | [文档](https://bailian.console.aliyun.com/?tab=doc#/doc/?type=model)              | [模型](https://bailian.console.aliyun.com/?tab=model#/model-market/all)      | 本课程主线平台，主要用于通义千问与 OpenAI 兼容接入 |
| **DeepSeek**   | [平台](https://platform.deepseek.com/)                 | [API-Key](https://platform.deepseek.com/api_keys)                   | [文档](https://api-docs.deepseek.com/zh-cn/)                                      | [模型](https://platform.deepseek.com/usage)                                  | 推理与代码能力强，本章用于多模型共存示例           |
| **OpenRouter** | [平台](https://openrouter.ai/)                         | [API-Key](https://openrouter.ai/settings/keys)                      | [文档](https://openrouter.ai/docs/community/frameworks-and-integrations-overview) | [模型](https://openrouter.ai/models)                                         | 多模型统一聚合平台，适合做“一个入口接多家模型”     |
| **硅基流动**   | [平台](https://www.siliconflow.cn/)                    | [API-Key](https://cloud.siliconflow.cn/me/account/ak)               | [文档](https://docs.siliconflow.cn/cn/userguide/capabilities/text-generation)     | [模型](https://cloud.siliconflow.cn/me/models)                               | 国内常见 AI API 平台，适合练手与接入开源模型       |
| **百度千帆**   | [平台](https://console.bce.baidu.com/qianfan/overview) | [API-Key](https://console.bce.baidu.com/qianfan/ais/console/apiKey) | [文档](https://cloud.baidu.com/doc/qianfan-docs/s/Mm8r1mejk)                      | [模型](https://console.bce.baidu.com/qianfan/modelcenter/model/buildIn/list) | 百度系模型平台                                     |
| **CloseAI**    | [平台](https://platform.closeai-asia.com/)             | [API-Key](https://platform.closeai-asia.com/)                       | [文档](https://doc.closeai-asia.com/tutorial/api/openai.html)                     | [模型](https://doc.closeai-asia.com/)                                        | OpenAI / 国际模型兼容接入平台之一                  |

---

## 3、安装依赖

### 3.1 推荐方式

如果你是跟着本仓库按章节学习，**最推荐的方式不是手动一个个装包，而是直接安装项目依赖**：

```bash
pip install -r requirements.txt
```

它能和本仓库案例保持一致，后续学到 Prompt、Parser、LCEL、Memory、RAG、Agent 时也不用再频繁补装依赖，还能避免“当前章节能跑、下一章突然缺包”的情况。

如果网络较慢，可用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.2 手动安装最小依赖

如果你只是想先跑通本章 HelloWorld，也可以安装最小依赖集合。
以本章案例为核心，建议至少安装：

```bash
# LangChain 主包
pip install langchain -i https://pypi.tuna.tsinghua.edu.cn/simple

# OpenAI 兼容接入（阿里百炼、OpenAI 兼容网关等常用）
pip install langchain-openai -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple

# 读取 .env
pip install python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 本项目后续大量案例会用到的核心抽象
pip install langchain-core -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果你要运行本章的 **DeepSeek 多模型共存案例**，还建议安装：

```bash
pip install langchain-deepseek -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> **说明**：本项目的 [requirements.txt](requirements.txt) 已包含 `langchain-deepseek`，所以如果你已经执行过 `pip install -r requirements.txt`，这里通常不需要再单独安装。

### 3.3 验证安装

安装完成后，建议先验证环境。这样可以提前发现“装错 Python”“装进了别的虚拟环境”“版本对不上”等问题。

**方法一：运行环境检查脚本**

【案例源码】环境检查脚本：`案例与源码-2-LangChain框架/01-helloworld/GetEnvInfo.py`

[GetEnvInfo.py](案例与源码-2-LangChain框架/01-helloworld/GetEnvInfo.py ":include :type=code")

这个脚本会输出：

- `langchain` 版本
- `langchain_community` 版本
- LangChain 实际安装路径
- 当前 Python 版本

它的价值在真实项目里非常大。因为很多“明明装了包却提示找不到”的问题，最后都是因为你运行脚本时用的不是同一个 Python 环境。

**方法二：用 PyCharm 查看已安装包**

在 PyCharm 的 **Python 软件包** 面板里，可以直接确认 `langchain`、`langchain-core`、`langchain-openai` 等包是否存在、版本是什么。

![PyCharm「Python 软件包」面板：查看已安装的 langchain、langchain-core、langchain-openai 等包及版本，用于核对是否装对虚拟环境](images/10/10-3-4-1.png)

---

## 4、案例：基于阿里百炼的 HelloWorld

### 4.1 调用三件套

无论你接的是百炼还是其他平台，真正写代码时都离不开三件套。这里用百炼做一次完整说明。

#### 4.1.1 获得 API Key

在百炼控制台的 **API-KEY 管理**中创建并复制密钥，通常形如 `sk-xxx`。

![阿里云百炼控制台：API-KEY 管理页创建与复制密钥（形如 sk-xxx）](images/10/10-4-1-1.jpeg)

#### 4.1.2 获得模型名

在模型广场或模型详情页里确认你真正要调用的模型标识，例如 `qwen-plus`、`qwen3-max` 等。

![百炼模型广场：浏览可选模型及在列表中展示的模型标识](images/10/10-4-1-2.jpeg)

![模型详情页：查看实际调用时使用的模型名（与界面展示名称可能略有差异，以详情/API 文档为准）](images/10/10-4-1-3.jpeg)

![模型名示例：如 qwen-plus、qwen3-max 等在代码 `model=` 中填写的字符串](images/10/10-4-1-4.jpeg)

#### 4.1.3 获得 Base URL

如果你走的是 OpenAI 兼容接法，就需要对应的兼容接口地址，例如：

![百炼文档或控制台：OpenAI 兼容模式的 Base URL（如 compatible-mode/v1 根地址）](images/10/10-4-1-5.jpeg)

当前课程里最常见的百炼 Base URL 是：

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

**本节小结**

| 项目         | 示例 / 说明                                         |
| ------------ | --------------------------------------------------- |
| **API Key**  | `sk-xxx`（在控制台创建）                            |
| **模型名**   | 如 `qwen-plus`、`qwen3-max`                         |
| **Base URL** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

### 4.2 HelloWorld 的最小心智模型

在写代码之前，先把最小链路想明白：

```text
准备三件套 → 初始化模型 → invoke("问题") → 读取 response.content
```

这里有两个关键词一定要先认识：

- `invoke()`：同步调用模型，返回一个消息对象
- `.content`：取出消息对象里的正文文本

也就是说：

- `invoke()` = “把问题发出去”
- `.content` = “把模型真正回答的文字取出来”

这就是本章最核心的最小调用链。

### 4.3 示例代码（0.3 与 1.x 两种写法）

这一节会保留两种写法，不是因为你新项目里都要用，而是因为现实里你一定会同时遇到两类资料：

- 老教程、老项目：经常还是 0.x / 经典写法
- 新项目、官方主线：更多使用 1.x 统一入口写法

#### 4.3.1 方式一：LangChain 0.3 / 经典写法

【案例源码】`案例与源码-2-LangChain框架/01-helloworld/LangChainV0.3.py`

[LangChainV0.3.py](案例与源码-2-LangChain框架/01-helloworld/LangChainV0.3.py ":include :type=code")

这个案例最有价值的地方有三点：

- 它展示了 **`ChatOpenAI` + `base_url`** 这种经典的 OpenAI 兼容接法
- 它明确对比了 **硬编码 Key → 环境变量 → `.env`** 三种配置方式
- 它让你看到 `invoke()` 返回的是一个对象，而不只是字符串

其中最重要的工程习惯是：**不要把 API Key 写死在代码里**。

#### 4.3.2 方式二：LangChain 1.x 推荐写法

【案例源码】`案例与源码-2-LangChain框架/01-helloworld/LangChainV1.0.py`

[LangChainV1.0.py](案例与源码-2-LangChain框架/01-helloworld/LangChainV1.0.py ":include :type=code")

这个案例是当前更推荐你重点掌握的写法。它最大的意义在于：通过 **`init_chat_model` 统一入口**，你不再需要为每个模型厂商记一套不同的初始化方式，而是先记住同一套调用骨架，再通过参数切换不同模型和 provider。

### 4.4 0.3 与 1.x 写法到底差在哪

这个问题必须讲透，否则你后面看旧代码会很乱。

**0.3 / 经典写法的思路**是：

- 直接从具体集成包导入类，例如 `ChatOpenAI`
- 类名本身就带有“我是按哪种协议接入”的语义
- 代码非常直观，但不同厂商、不同类名会让项目越写越散

**1.x 的思路**是：

- 用 `init_chat_model` 作为统一入口
- 通过 `model`、`model_provider`、`api_key`、`base_url` 等参数描述“我要接谁”
- 同一套代码骨架更容易迁移、统一与维护

你可以这样记：

| 维度           | 0.3 / 经典写法             | 1.x / 推荐写法         |
| -------------- | -------------------------- | ---------------------- |
| **入口**       | `ChatOpenAI(...)` 等具体类 | `init_chat_model(...)` |
| **特点**       | 简单直接、旧资料常见       | 统一入口、适合新项目   |
| **适合做什么** | 读懂旧教程、兼容旧代码     | 作为当前主学习路线     |

这里补充一个真实项目建议：

> 如果你现在是从零开始做新项目，优先学 **1.x 写法**；如果你是在维护现有项目，能读懂 **0.3 / 经典写法** 同样非常重要。

---

## 5、案例：多模型共存（通义 + DeepSeek）

### 5.1 为什么真实项目经常不是“只接一个模型”

现实项目里，多模型共存反而是常态。原因很简单：

- 不同模型的成本不同
- 不同模型的强项不同
- 不同业务场景对稳定性、速度、推理能力的要求不同

例如：

- 日常客服问答，用一个便宜稳定的模型
- 复杂推理或代码生成，用更擅长推理的模型
- 某些企业还会同时保留在线模型和本地模型作为备选

所以，多模型共存不是“进阶玩法”，而是非常现实的工程需求。

### 5.2 调用三件套

#### 5.2.1 获得 API Key

在 DeepSeek 控制台创建并复制 Key。

![DeepSeek 开放平台：API Key 创建、查看与管理入口](images/10/10-5-2-1.jpeg)

#### 5.2.2 获得模型名

当前 DeepSeek API 官方主推的模型名包括：

- `deepseek-v4-flash`：适合作为默认示例模型，兼顾速度与成本。
- `deepseek-v4-pro`：适合更复杂的推理、代码和高质量生成场景。

> 说明：DeepSeek 官方文档已将 `deepseek-chat` 和 `deepseek-reasoner` 标注为兼容别名，它们会在 2026-07-24 弃用。新写代码时，优先以官方当前模型列表里的 `deepseek-v4-flash`、`deepseek-v4-pro` 等模型名为准。

![DeepSeek 文档或控制台：模型列表与调用名示意（如 deepseek-v4-flash、deepseek-v4-pro）](images/10/10-5-2-2.jpeg)

#### 5.2.3 获得 Base URL

常见写法为：

```text
https://api.deepseek.com
```

具体仍应以 DeepSeek 官方文档为准。

![DeepSeek：普通对话模式与推理（reasoner）模式的适用场景说明示意](images/10/10-5-2-3.jpeg)

### 5.3 多模型共存示例代码

【案例源码】`案例与源码-2-LangChain框架/01-helloworld/LangChain_MoreV1.0.py`

[LangChain_MoreV1.0.py](案例与源码-2-LangChain框架/01-helloworld/LangChain_MoreV1.0.py ":include :type=code")

这个案例有三个特别重要的知识点：

1. **同一个脚本里可以同时创建多个模型实例**
2. **每个实例可以有自己的模型名、API Key、Base URL、provider**
3. **变量名要区分清楚**，例如 `llm_qwen`、`llm_deepseek`，避免后一个把前一个覆盖掉

它其实已经很接近真实项目了。因为正式项目里，我们很少只保留一个模型对象，而是会把多个模型按用途封装起来，例如：

- 默认问答模型
- 高级推理模型
- 便宜快速模型
- 备用降级模型

---

## 6、实战：企业级封装与流式输出

### 6.1 为什么 HelloWorld 跑通后还不够

如果你只是做一个临时脚本，HelloWorld 那种“写几行代码直接调模型”的方式已经够用了。  
但只要你想把它放进真实项目，就会马上遇到这些问题：

- API Key 是否配置正确
- 日志打在哪里
- 出错时怎么区分“配置错误”和“模型调用错误”
- 模型初始化是不是每个文件都要重复写
- 网页端或终端能不能边生成边显示

这就是为什么本章最后一节要引入“**企业级封装**”和“**流式输出**”。

### 6.2 invoke() 与 stream() 的区别

这是初学者最先会用到的两种调用方式。

`invoke()`：一次性返回完整结果。  
适合：

- 简单问答
- 后台处理
- 不需要实时展示中间输出的场景

`stream()`：边生成边返回。  
适合：

- 命令行实时输出
- 聊天界面打字机效果
- 长文本生成
- 用户等待体验更敏感的场景

最小示例：

```python
for chunk in model.stream("请介绍一下 LangGraph"):
    print(chunk.content, end="")
```

可以这样记：

- `invoke()`：等模型全部想完，再一次性告诉你答案
- `stream()`：模型边想边说，你一边接一边显示

### 6.3 示例代码（封装、异常、流式）

【案例源码】`案例与源码-2-LangChain框架/01-helloworld/StandardDesc.py`

[StandardDesc.py](案例与源码-2-LangChain框架/01-helloworld/StandardDesc.py ":include :type=code")

这个案例比前面的 HelloWorld 更接近真实项目，主要体现在：

- **把模型初始化封装成函数**，避免到处重复写配置
- **显式检查环境变量**，减少“Key 为空还去请求”的低级错误
- **使用日志**，而不是只靠 `print`
- **区分异常类型**，便于排查问题
- **同时演示 `invoke()` 与 `stream()`**

如果说前面的案例是在教你“怎么调通”，这个案例就在教你“怎么写得像一个真正的项目”。

---

**章节思考题：**

1. LangChain 第一次调用最小闭环里，为什么 **API Key、模型名、Base URL** 缺一不可？

   **答案：** 因为这三者分别解决认证、选用哪个模型、请求发到哪里三个最基础问题。少任何一个，程序都无法把请求正确地发送给目标模型服务。

2. `invoke()` 和 `stream()` 在用户体验和程序处理方式上最大的差别是什么？

   **答案：** `invoke()` 一次性拿到完整结果，处理更简单；`stream()` 是边生成边返回，用户体感更快，但程序需要处理分片、结束事件和可能的中途异常。

3. 为什么本仓库建议你尽量在项目根目录运行案例，而不是直接在案例子目录运行？

   **答案：** 因为仓库很多示例默认依赖根目录下的 `.env`、相对路径和统一依赖环境。直接在子目录运行，最容易出现环境变量读不到、模块导入失败或路径错位。

4. 如果团队里一位新同学“第一个 LangChain 脚本一直跑不通”，你会按什么顺序帮他排查环境、依赖和模型配置问题？

   **答案：** 我会先确认 Python 环境和依赖是否安装正确，再核对 `.env`、API Key、模型名和 Base URL，随后跑最小 Demo 看是导入问题、认证问题还是模型接口问题，最后再看日志和返回报错定位细节。

5. 如果把本章的 HelloWorld Demo 升级成团队可复用模块，你觉得最先应该补上的工程能力是什么？为什么？

   **答案：** 最先应该补的是统一配置和异常处理，把 API Key、模型名、Base URL、超时、重试、日志这些公共能力抽出来。这样团队后面接更多模型或更多案例时，才不会每个脚本都各写一套。

**本章小结：**

- **HelloWorld 的本质**不是“写一个很简单的例子”，而是验证整条调用链是否打通。对 LangChain 来说，这条最小链路就是：**准备 API Key、模型名、Base URL → 初始化模型 → `invoke()` 调用 → `.content` 取回复**。
- 本章建议按 **LangChain 1.x** 语境学习，并遵循本项目当前环境约定：**Python 3.10–3.13，推荐 3.10**。如果是跟着本仓库学，优先执行 `pip install -r requirements.txt`；如果只想跑本章最小案例，至少安装 `langchain`、`langchain-openai`、`openai`、`python-dotenv`、`langchain-core`，运行 DeepSeek 多模型案例时建议补 `langchain-deepseek`。
- 本章保留的全部案例，分别对应了不同学习目标：`GetEnvInfo.py` 用于**检查环境**，`LangChainV0.3.py` 与 `LangChainV1.0.py` 用于理解 **经典写法与 1.x 写法**，`LangChain_MoreV1.0.py` 用于掌握 **多模型共存**，`StandardDesc.py` 则让你迈出从“教学 Demo”走向“工程化写法”的第一步。

**建议下一步：** 先亲手跑通本章至少两个脚本，推荐顺序是：`GetEnvInfo.py` → `LangChainV1.0.py` → `LangChain_MoreV1.0.py` → `StandardDesc.py`。跑通之后，马上进入 [第 11 章 Model I/O 与模型接入](11-Model-I-O与模型接入.md)，把这章中“会用”的部分升级成“真正理解为什么这样接、不同模型如何统一接入”。等你再接着学 [第 13 章 提示词与消息模板](13-提示词与消息模板.md) 和 [第 14 章 输出解析器](14-输出解析器.md)，就能形成完整的 **输入 → 模型 → 输出** 学习闭环。
