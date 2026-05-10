# 6 - Coze 的 Windows 平台部署

本章偏**实操部署**：在 Windows 上把开源版 Coze（扣子）跑起来，实现**本地/私有化**使用 Coze Studio 开发智能体，并可选部署 Coze Loop（扣子罗盘）做提示词评测与运维。硬件要求亲民，普通电脑（2 核 CPU + 4GB 内存）即可。

---

**本章课程目标：**

- 理解 Coze 开源后，为什么它在私有化、B 端交付、内网场景里有现实价值。
- 分清 Coze 的两个核心组件：**Coze Studio** 负责开发与调试，**Coze Loop** 负责评测、实验、Trace 和运维。
- 完成 **Coze Studio** 在 Windows 上的最小部署：安装 Docker -> 获取代码 -> 配置模型 -> `docker compose` 启动 -> 浏览器访问。
- 理解两条常见模型接入路线：**云端 API 模型** 与 **本地 Ollama 模型**，知道它们分别适合什么场景。
- 对 Coze Loop 建立初步认识，知道它为什么更偏“后期评测与运营”，而不是“第一天就必须装”。

**学习建议：** 先通读第 1 节把握「四阶段：环境准备 → 获取代码 → 配置模型 → 启动服务」；第 2 节按顺序做（Docker → 下载 Studio → 二选一配置模型 → 启动）。模型配置是核心：选火山方舟则需在火山引擎创建 API Key 和 Endpoint；选 Ollama 则需先装 Ollama 并拉取模型。Coze Loop 为进阶，可先只部署 Studio 跑通再学 Loop。

---

## 1、整体概述

### 1.1 Coze 的开源

字节跳动于 2025 年 7 月 26 日开源其 AI 智能体开发平台 Coze（中文名“扣子”），短短 48 小时内 GitHub 星标数突破 9000+。

最大亮点在于其极致亲民的硬件要求——普通家用电脑（`2核CPU+4GB内存`）即可流畅运行。

**为什么 Coze 开源是劲爆新闻？**

之前我们在 Coze 上搭建的智能体只能交付给 C 端用户，如果交付给 B 端用户通常都是用 Dify、n8n 等平台上搭建智能体交付，因为企业用户要求`数据绝对安全`，放在公网上是不能接受的，而 Dify 恰好是可以私有化部署的。

现在 Coze 也开源了，意味着以后更多了一种选择，这绝对可以说是一个里程碑式的进步。

**为什么选择开源 Coze？**

- 零成本商用：采用 Apache 2.0 协议，意味着你可以自由地用于商业用途，并进行二次开发
- 全链路开源：覆盖 Agent 开发（Studio）、测试/运维（Loop）、部署（SDK）
- 硬件平民化：告别动辄 16G 显存的 GPU，普通笔记本即可运行 AI 工作流

### 1.2 两大核心组件：Coze Studio 和 Coze Loop

这一章最容易混乱的地方，是把 Studio 和 Loop 混成一回事。其实它们解决的是不同层的问题。

**1. Coze Studio：开发入口**

- 用来创建 Agent、工作流、工具调用、模型配置
- 更适合“把应用做出来”
- 对本章来说，它是最主要的部署目标

**2. Coze Loop：评测与运维入口**

- 用来做 Prompt 调试、评测集、实验对比、Trace 追踪、自动化评测
- 更适合“把效果测清楚、把运行过程管起来”
- 它不是第一天必须安装，但是真实项目里非常有价值

你可以这样记：

- **Studio = 开发环境**
- **Loop = 评测与运维环境**

### 1.3 本章部署主线：先抓住四步

无论是 Coze Studio 还是 Coze Loop，初次学习时都建议先抓住这条统一主线：

| 阶段        | 你真正要完成的事                | 关键说明                                  |
| ----------- | ------------------------------- | ----------------------------------------- |
| 1. 环境准备 | 安装 Docker，必要时安装 Git、Go | Docker 是前置条件，Loop 还会额外用到 Go   |
| 2. 获取代码 | 下载或克隆官方仓库              | GitHub 慢时可用 ZIP、Gitee 镜像或课程资料 |
| 3. 配置模型 | 选云端 API 或本地 Ollama        | 这是最关键也最容易出错的一步              |
| 4. 启动服务 | 执行 Docker 命令并浏览器访问    | 跑起来后再看页面和模型是否联通            |

这条主线后面会在多处重复出现，因为它本质上就是平台部署的通用套路。

### 1.4 云端模型和本地模型到底怎么选

模型配置是本章真正的核心。很多同学以为“Docker 起起来就算部署成功”，其实不对。**平台起起来只是第一步，模型接通才意味着你能真正创建和运行智能体。**

| 配置方式         | 优点                                 | 缺点                                             | 更适合谁                           |
| ---------------- | ------------------------------------ | ------------------------------------------------ | ---------------------------------- |
| 云端 API 模型    | 能力强、响应快、配置相对直接         | 需要联网，通常有调用成本，数据会经过云端服务商   | 学习、测试、快速验证               |
| 本地 Ollama 模型 | 数据更可控，离线可用，不依赖外部 API | 对本机硬件要求更高，模型能力和速度取决于本地资源 | 内网、隐私敏感、想完全掌控模型的人 |

所以不要把它理解成“哪种更高级”，而要理解成“哪种更适合当前目标”：

- 想**最快跑起来**：优先云端 API
- 想**更私有、更可控**：再走 Ollama

> **可这样记：** 部署 Coze 就四步：**环境 -> 代码 -> 模型 -> 启动**。其中最关键的不是 Docker 本身，而是“模型有没有真正配通”。如果页面能打开但看不到模型、调不了应用，优先检查的通常不是前端，而是模型配置文件里的 `api_key`、`model`、`endpoint` 或本地模型服务状态。

## 2、Coze Studio 的安装和配置

![Coze Studio 本地部署四阶段流程总览图](images/6/6-2-1-1.png)

### 2.1 安装 Docker（环境准备）

**Docker 是唯一前置依赖**，用于创建隔离运行环境：

如果你对镜像、容器、Compose、volume、端口映射这些概念还不熟，可以先看 [第 8.1 章 Docker 入门与 Dify 部署排障](8.1-Docker入门与Dify部署常见问题.md)。本章只保留 Coze 部署所需步骤，不再重复展开 Docker 基础。

#### ① 下载安装包

- Docker 官网下载地址：https://www.docker.com/products/docker-desktop/
- 国内用户若下载慢，可使用飞书镜像包：https://ay6exk7fyt.feishu.cn/drive/folder/IccNf2B4JlJOIvd2kWfcpYnRn4l

![Docker Desktop 官方下载页面](images/6/6-2-1-2.png)

#### ② 安装设置及启动

![Docker Desktop 安装设置界面](images/6/6-2-1-3.png)

![Docker Desktop 安装过程界面](images/6/6-2-1-4.png)

安装完成后打开 Docker Desktop，确认状态栏显示 **“Running”** ✅

![Docker Desktop 运行状态为 Running 的界面](images/6/6-2-1-5.png)

![Docker Desktop 成功启动后的主界面](images/6/6-2-1-6.png)

> 个别首次安装的小伙伴会被 Windows 系统提示需要安装`适用于Linux的Windows子系统`。这里选择确认安装。稍等片刻后会完成安装。

#### ③ 配置镜像加速器或 docker 代理

在安装 Coze 之前，我们要先进行 Docker 中镜像网站的设置，因为默认的镜像是国外的网址，访问不到或比较慢。需要设置镜像加速器或 Docker 代理。

> 说明：如果大家设置过代理，那么推荐方式 2。如果没有，则使用方式 1。

##### 方式 1：配置镜像加速器

![Docker Desktop 中配置镜像加速器的界面](images/6/6-2-1-7.png)

通用排查思路见：[第 8.1 章 - 网络慢或镜像拉取失败](8.1-Docker入门与Dify部署常见问题.md#_12、网络慢或镜像拉取失败)。

##### 方式 2：配置 Docker 代理

![Docker Desktop 中配置代理的界面](images/6/6-2-1-8.png)

![Docker Desktop 中填写代理地址和端口的界面](images/6/6-2-1-9.png)

将 **7890** 改为你本地代理软件实际监听的端口（若代理端口不是 7890）。

到这里，Docker 已经安装配置好了。

### 2.2 安装 Coze Studio

#### ① 下载 Coze 安装包

##### 方式 1：Github/Gitee

1. 打开 Docker Desktop 内置终端（右下角 Terminal 图标）
2. 执行以下命令：

```bash
# 克隆官方仓库代码
git clone https://github.com/coze-dev/coze-studio.git
```

**注意：** 由于 GitHub 下载较慢，可将 GitHub 上的 coze-studio 仓库镜像到 Gitee，再从 Gitee 克隆。步骤如下：

1）在 Gitee 上导入仓库：

![Gitee 导入 Coze Studio 仓库的界面](images/6/6-2-2-1.png)

2）复制 GitHub 上的 coze-studio 仓库地址

![GitHub 上 Coze Studio 仓库地址的界面](images/6/6-2-2-2.png)

粘贴到：

![Gitee 中填写 Coze Studio 仓库地址的界面](images/6/6-2-2-3.png)

3）导入完成后，复制 Gitee 上的仓库地址：

![Gitee 中已导入 Coze Studio 仓库的界面](images/6/6-2-2-4.png)

> 大家可以直接粘贴如下地址：
>
> git clone https://gitee.com/shkstart/coze-studio.git

粘贴到 Docker Desktop 客户端：

![在 Docker Desktop 终端中克隆 Coze Studio 仓库的界面](images/6/6-2-2-5.png)

> 说明：git 是一个从代码仓库拉取代码的工具，大家通过以下网址下载，安装一下即可。安装非常简单，安装以后，就可以使用 git 命令了。如果你没有安装 git，请先安装 git：https://git-scm.com/downloads

##### 方式 2：解压 zip 包

若不想安装 Git，也可直接从 GitHub 下载 coze-studio 的 ZIP 包，如下图：

https://github.com/coze-dev/coze-studio

![GitHub 下载 Coze Studio ZIP 包的界面](images/6/6-2-2-6.png)

下载后解压到指定目录即可。

#### ② 安装并配置模型

首次部署并启动 Coze Studio 开源版本之前，需要在 Coze Studio 项目中配置模型服务。否则，在创建 Agent 或工作流时将无法正确选择模型。

1、从模板目录复制 doubao-seed-1.6 模型的模板文件，并粘贴到配置文件目录中。

首先，进入根目录 coze-studio 下，在地址栏中输入“cmd”并按回车键。

![在 Coze Studio 根目录地址栏输入 cmd 的界面](images/6/6-2-2-7.png)

执行命令：

```bash
copy backend\conf\model\template\model_template_ark_doubao-seed-1.6.yaml backend\conf\model\ark_doubao-seed-1.6.yaml
```

2、修改配置文件目录中的模板文件，填入对应的参数

`id`：Coze Studio 中的模型 ID，由开发者自主定义，必须为非零整数，全局唯一。模型上线后请勿修改模型 ID。
`meta.conn_config.api_key`：在线模型服务的 API Key，获取方式见下方「1、创建 API Key」。
`meta.conn_config.model`：在线模型服务的模型 ID。本例中为火山方舟接入点的 **Endpoint ID**，获取方式见下方「2、创建 Endpoint」。

**配置方案说明：**

模型配置是部署的核心，主要有以下两种方案，根据自己的需求（如网络条件、数据敏感性、成本）进行选择。

| 配置方式                   | 优点                                           | 缺点                                                                 | 适用场景                                                 |
| :------------------------- | :--------------------------------------------- | :------------------------------------------------------------------- | :------------------------------------------------------- |
| 云端 API 模型 (如火山方舟) | 模型能力强，响应速度快，无需消耗本地计算资源。 | 需要 API Key（可能产生费用），需要联网，数据需传输到厂商云端。       | 体验 Coze 全部功能，需要最先进的模型能力，开发测试环境。 |
| 纯本地模型 (通过 Ollama)   | `数据完全私密`，离线可用，API 调用`免费`。     | 本地硬件要求较高（尤其需要较好 GPU），模型性能可能不及顶级云端模型。 | 对数据安全有严格要求，内网环境，希望完全掌控模型的场景。 |

##### 方案 1：配置云端 API 模型（以火山方舟为例）

**1、创建 API Key**

进入火山引擎官网 https://www.volcengine.com ，打开【控制台】。

![火山引擎控制台首页界面](images/6/6-2-2-8.png)

搜索并进入【火山方舟】

![在火山引擎中进入火山方舟的界面](images/6/6-2-2-9.png)

点击【API Key 管理】下的【创建 API Key】，选择【创建】

![火山方舟创建 API Key 的界面](images/6/6-2-2-10.png)

点击小眼睛即可查看 API Key ，复制备用。

![火山方舟查看 API Key 的界面](images/6/6-2-2-11.png)

**2、创建 Endpoint**

进入【在线推理】页面，选择【自定义推理接入点】，点击【创建推理接入点】

![火山方舟创建推理接入点的界面](images/6/6-2-2-12.png)

输入接入点名称，建议以模型命名，点击【添加模型】

![火山方舟设置推理接入点名称并添加模型的界面](images/6/6-2-2-13.png)

模型目前支持：豆包、DeepSeek、Kimi、Qwen，这里以豆包 1.6 为例，选择后确定。

![火山方舟选择豆包模型接入点的界面](images/6/6-2-2-14.png)

或

![火山方舟添加模型的备选入口界面](images/6/6-2-2-15.png)

勾选协议，点击【开通模型并接入】。

![火山方舟勾选协议并开通模型接入的界面](images/6/6-2-2-16.png)

补充：如果是模型首次开通需要实名认证，输入个人信息，手机刷脸验证。

复制 Endpoint。注意：模型名称下方的 ID 就是 Endpoint。

![火山方舟复制 Endpoint ID 的界面](images/6/6-2-2-17.png)

**3、配置 Coze 文件**

找到前面的文件：ark_doubao-seed-1.6.yaml，进行编辑

- id 修改为任意 5 位以上纯数字。

![编辑 Coze Studio 模型配置文件的界面](images/6/6-2-2-18.png)

- 将前面创建的【API Key】和【Endpoint】填入下图位置内，保存并关闭文件。

![在 Coze Studio 模型配置文件中填写 API Key 和 Endpoint 的界面](images/6/6-2-2-19.png)

##### 方案 2：配置纯本地模型（通过 Ollama）

这种方法可以实现完全离线的私有化部署。

**1、安装 Ollama**：首先在本地安装 Ollama，它是一个用于在本地运行大模型的工具。

**2、拉取模型**：通过 Ollama 拉取你想要的模型，例如在命令行中执行 `ollama pull qwen2.5:7b`来下载一个开源模型。

**3、配置 Coze**：在 Coze 项目目录下，找到 Ollama 的配置文件模板 model_template_ollama.yaml，

![本地安装 Ollama 并准备拉取模型的界面](images/6/6-2-2-20.png)

将其复制并重命名为 model_ollama.yaml，保存到 backend/conf/model/ 目录下：

![复制 Ollama 模型配置模板文件的界面](images/6/6-2-2-21.png)

修改其中的 base_url 为 Ollama 的服务地址（通常是 `http://host.docker.internal:11434`），并指定你拉取的 model 名称。

![修改 Ollama 模型配置文件 base_url 和 model 的界面](images/6/6-2-2-22.png)

#### ③ 安装并启动 Coze

下图中有一个名为 **docker** 的目录，需要进入该目录进行后续安装。

![Coze Studio 项目中 docker 目录位置的界面](images/6/6-2-2-23.png)

进入 **coze-studio\docker** 目录后，可按以下步骤验证环境：

**1、** 在终端输入 `docker` 并回车，若出现下图类似结果，说明 Docker 已正确安装。

![在终端中验证 Docker 是否安装成功的界面](images/6/6-2-2-24.png)

**2、环境变量配置**

执行如下命令，重命名环境配置文件：

```bash
copy .env.example .env
```

> Windows 下使用 `copy`；Linux/Mac 下可使用 `cp .env.example .env`。

![将 Coze Studio 的 .env.example 复制为 .env 的界面](images/6/6-2-2-25.jpeg)

**3、在 Docker 里启动 Coze**

首次启动可能需要 5-10 分钟（依赖网络速度），运行一下这条命令：

```bash
docker compose --profile '*' up -d
```

![在 Docker 中启动 Coze Studio 的命令行界面](images/6/6-2-2-26.png)

> 这条命令的核心是：在 Coze 的 `docker` 目录中，通过 Compose 启用所有 profile 并后台启动服务。`docker compose up -d` 的通用含义见 [第 8.1 章](8.1-Docker入门与Dify部署常见问题.md#_3、compose-到底做了什么)。

出现下图表示成功：

![Coze Studio 启动成功后的日志界面](images/6/6-2-2-27.png)

**4、安装结束后，查看运行状态**

```bash
docker compose ps
```

也可打开 Docker Desktop，在容器列表中确认各服务已处于运行状态。

![查看 Coze Studio 容器运行状态的界面](images/6/6-2-2-28.png)

#### ④ 访问 Coze Studio 界面

安装完成后，在浏览器中访问 http://localhost:8888/ 即可打开 Coze Studio，界面如下。

![浏览器访问 Coze Studio 时的登录界面](images/6/6-2-2-29.png)

登录后即可正常使用。

![登录后的 Coze Studio 主界面](images/6/6-2-2-30.png)

> 小遗憾：目前功能较商业版还比较简陋，但未来可期！

## 3、Coze Loop（扣子罗盘）指南

### 3.1 介绍

![Coze Loop 产品介绍界面](images/6/6-3-1-1.png)

扣子罗盘通过提供全生命周期的管理能力，帮助开发者更高效地开发和运维 AI Agent。无论是提示词工程、AI Agent 评测，还是上线后的监控与调优，扣子罗盘都提供了强大的工具和智能化的支持，极大地简化了 AI Agent 的开发流程，提升了 AI Agent 的运行效果和稳定性。

### 3.2 部署

#### ① 准备工作

安装 **Coze Loop** 开源版之前，请确保软硬件环境满足以下要求：

**1、Go 语言环境**：已安装 Go SDK，版本为 1.23.4 及以上。配置 GOPATH，并将 `${GOPATH}/bin` 加入系统环境变量 PATH，以便安装的二进制工具可被找到并运行。

Go 语言官网：https://go.dev/dl/

![Go 语言官网下载页面](images/6/6-3-2-1.png)

下载完成后双击运行安装程序。

![Go 安装程序启动界面](images/6/6-3-2-2.png)

按提示一路点击“Next”即可。

安装完成后，确保 Go 安装目录下的 bin 目录（或 GOPATH/bin）已在环境变量 PATH 中。

![Go 安装完成后的环境变量配置示意图](images/6/6-3-2-3.png)

**2、Docker 环境**：提前安装 Docker、Docker Compose，并启动 Docker 服务

**3、模型**：已开通 OpenAI 或火山方舟等在线模型服务。

#### ② 下载/克隆仓库

此处推荐方式 1。方式 2（git clone）在后续 ⑤ 启动服务时可能报错，若遇问题可改用方式 1。

比如：

![Coze Loop 仓库下载方式示意图](images/6/6-3-2-4.png)

##### 方式 1：下载 zip 文件(推荐)

从 GitHub 下载 Coze Loop 的 zip 文件到本地，解压即可（解压后目录名可能为 `coze-loop-main`）。

```
https://github.com/coze-dev/coze-loop
```

![GitHub 下载 Coze Loop ZIP 包的界面](images/6/6-3-2-5.png)

我存放到了如下路径：

![本地保存 Coze Loop 压缩包的目录界面](images/6/6-3-2-6.png)

##### 方式 2：克隆仓库

```bash
git clone https://gitee.com/shkstart/coze-loop.git
```

![通过 Gitee 克隆 Coze Loop 仓库的界面](images/6/6-3-2-7.png)

#### ③ 配置模型

编辑文件 coze-loop-main\release\deployment\docker-compose\conf\model_config.yaml，修改 api_key 和 model 字段。以火山方舟为例：

- api_key：火山方舟 API Key。（参考 Coze Studio 中的同步骤情况）
- model：火山方舟模型接入点的 Endpoint ID。（参考 Coze Studio 中的同步骤情况）

![配置 Coze Loop model_config.yaml 的界面](images/6/6-3-2-8.png)

#### ④ 更改端口

1、打开 coze-loop-main\release\deployment\docker-compose 目录下的.env，将 `COZE_LOOP_APP_OPENAPI_PORT` 改为 `8889` 或其他未被占用的端口。

![修改 Coze Loop .env 端口配置的界面](images/6/6-3-2-9.png)

2、打开 `coze-loop-main/release/deployment/docker-compose` 目录下的 `docker-compose.yml`，将其中引用 `${COZE_LOOP_APP_OPENAPI_PORT}` 的端口与 `.env` 中的 `COZE_LOOP_APP_OPENAPI_PORT` 保持一致（如 8889）。

![修改 Coze Loop docker-compose 端口映射的界面](images/6/6-3-2-10.png)

#### ⑤ 启动服务

在 coze-loop-main\release\deployment\docker-compose 目录下执行以下命令，使用 Docker Compose 快速部署 Coze Loop 开源版。

```cmd
docker compose -f docker-compose.yml --env-file .env --profile "*" up -d
```

若希望在前台运行以便查看完整日志（关闭终端窗口后进程会退出），可去掉 `-d`。首次启动建议不加 `-d`，便于观察启动过程。

首次启动推荐命令

```cmd
docker compose -f docker-compose.yml --env-file .env --profile "*" up
```

首次启动需要拉取镜像、构建本地镜像，可能耗时较久。看到以下日志，则部署完成。

![Coze Loop 首次启动时的日志界面](images/6/6-3-2-11.png)

![Coze Loop 启动完成后的日志界面](images/6/6-3-2-12.png)

在 Docker Desktop 的容器列表中，除 xxx-init 等初始化容器（执行完后会自动退出）外，其余服务容器应均为运行状态，即表示部署成功。

#### ⑥ 访问 CozeLoop 开源版

在浏览器中访问 **http://localhost:8082** 即可打开 Coze Loop 开源版。

![Docker Desktop 中 Coze Loop 容器运行状态的界面](images/6/6-3-2-13.png)

注册完成后即可进入应用详情页。

![浏览器访问 Coze Loop 开源版时的界面](images/6/6-3-2-14.png)

### 3.3 Coze Loop 的使用

这里演示在线版本：https://www.coze.cn/loop

Coze Loop 官方提供了一些示例，位于在线版的 **Demo 空间**。

![Coze Loop 在线版 Demo 空间界面](images/6/6-3-3-1.png)

#### 功能 1：Prompt 开发

该模块用于提示词的预览与调试。

![Coze Loop 的 Prompt 开发模块界面](images/6/6-3-3-2.png)

点击详情

![Coze Loop Prompt 开发详情入口界面](images/6/6-3-3-3.png)

![Coze Loop Prompt 开发详情页界面](images/6/6-3-3-4.png)

#### 功能 2：Playground

该模块和 Prompt 开发功能类似，区别在于**自由对比模式**。

![Coze Loop Playground 模块界面](images/6/6-3-3-5.png)

在官方 Demo 空间中无法开启自由对比模式，可切换到个人空间使用。

![Coze Loop 在 Demo 空间中的 Playground 界面](images/6/6-3-3-6.png)

![Coze Loop 切换到个人空间的界面](images/6/6-3-3-7.png)

![Coze Loop 自由对比模式的界面](images/6/6-3-3-8.png)

#### 功能 3：评测集

该模块用于管理评测数据集。

![Coze Loop 评测集模块界面](images/6/6-3-3-9.png)

![Coze Loop 评测集详情界面](images/6/6-3-3-10.png)

![Coze Loop 新建评测集的界面](images/6/6-3-3-11.png)

#### 功能 4：评估器

该模块用于构建评估**Prompt 开发**实例的工具，本质上也是添加了提示词的大模型。

![Coze Loop 评估器模块界面](images/6/6-3-3-12.png)

![Coze Loop 新建评估器的界面](images/6/6-3-3-13.png)

本质上也是**提示词+大模型**

![Coze Loop 评估器配置详情界面](images/6/6-3-3-14.png)

#### 功能 5：实验

该模块用于创建和管理实验。

![Coze Loop 实验模块界面](images/6/6-3-3-15.png)

同样地，Demo 空间无权创建实验，切换到个人空间即可。

![Coze Loop 切换到个人空间创建实验的界面](images/6/6-3-3-16.png)

实验详情如下。

![Coze Loop 实验详情页界面](images/6/6-3-3-17.png)

**指标统计**模块以可视化方式展示评估结果。

![Coze Loop 实验指标统计界面](images/6/6-3-3-18.png)

新建实验

![Coze Loop 新建实验的界面](images/6/6-3-3-19.png)

依次设置基础信息、评测集、评测对象、评估器即可。

#### 功能 6：Trace

该模块记录了详细的运行信息。

![Coze Loop Trace 模块界面](images/6/6-3-3-20.png)

![Coze Loop Trace 详情界面](images/6/6-3-3-21.png)

![Coze Loop Trace 运行明细界面](images/6/6-3-3-22.png)

#### 功能 7：统计

该模块统计整个空间的运行情况。

#### 功能 8：自动化任务

该模块用于创建和管理自动化评测任务。

![Coze Loop 自动化任务模块界面](images/6/6-3-3-23.png)

详情页

![Coze Loop 自动化任务详情页界面](images/6/6-3-3-24.png)

![Coze Loop 自动化任务配置明细界面](images/6/6-3-3-25.png)

---

**章节思考题：**

1. Coze Studio 和 Coze Loop 在定位上最大的区别是什么？

   **答案：** Coze Studio 更偏开发环境，用来搭智能体、工作流和模型配置；Coze Loop 更偏运维和评测，用来做 Prompt 实验、数据集评估、Trace 和生命周期管理。前者解决“怎么做”，后者解决“怎么测、怎么管”。

2. 为什么说本地部署平台不等于问题就都解决了，模型接入和运维仍然是关键环节？

   **答案：** 因为平台只是壳，真正能不能跑起来还取决于模型是否接通、配置是否正确、容器是否稳定、资源是否够用。也就是说，本地部署解决的是可控性和私有化，不会自动替你解决模型可用性和运维问题。

3. 在模型配置时，云端 API 路线和 Ollama 路线最大的差异分别体现在哪？

   **答案：** 云端 API 路线的核心是配置好服务商的 Key 和 Endpoint，由远端提供算力；Ollama 路线的核心是模型在本机运行，需要本地拉取模型、关注硬件资源和推理性能。一个偏“接服务”，一个偏“自己跑模型”。

4. 如果你要向团队解释“为什么有了云端 Coze，还要看本地部署”，你会如何从数据、安全、交付方式三个角度说明？

   **答案：** 可以这样解释：本地部署的价值主要在于数据更可控、安全边界更清晰、交付方式更适合内网或私有化场景；同时它能让企业把平台、模型和业务系统整合成自己的基础设施，而不是完全依赖外部云平台。

5. 如果部署失败，你会如何按环境、代码、模型配置、容器状态四个层次做排查？

   **答案：** 我会按四层排查：先看环境是否满足 Docker、网络和端口条件；再看代码或配置文件是否放对、改对；然后检查模型服务是否真的可连、参数是否正确；最后看容器日志和运行状态，确认到底是启动失败、模型不可用还是前端访问问题。

**本章小结：**

- **本地部署意义**：Coze 开源让智能体平台不再只适合 C 端体验，也能进入更强调数据安全和私有化交付的场景。
- **核心组件**：Coze Studio 负责智能体开发，Coze Loop 更偏评测、实验、Trace 和运维，是更靠后的工程能力。
- **实操主线**：这章最关键的不是记住所有截图，而是掌握一条部署逻辑：**准备环境 -> 获取代码 -> 配置模型 -> 启动服务 -> 浏览器验证**。

**建议下一步：** 如果你更关心 Dify 的本地部署体验，可以对照学习 [第 7 章 Dify 的 Windows 平台部署](7-Dify的Windows平台部署.md)；如果你要继续看更完整的企业部署链路，再进入 [第 8 章 企业级大模型部署](8-企业级大模型部署.md)。
