# 7 - Dify 的 Windows 平台部署

本章偏**实操部署**：在 Windows 上把 Dify 跑在本地，实现**私有化**使用 Dify 开发 Agent、工作流和 RAG 应用。流程比 [第 6 章 Coze 部署](6-Coze的Windows平台部署.md) 更简单，核心就是「装 Docker → 拿代码 → 改配置 → 一条命令启动」。

---

**本章课程目标：**

- 理解为什么个人学习或企业内网场景会选择本地部署 Dify。
- 在 Windows 上完成 Docker Desktop 安装，并知道首次安装时为什么常会遇到 WSL 相关提示。
- 获取 Dify 项目，进入 `docker` 目录，复制 `.env.example` 为 `.env` 并完成最小配置。

**学习建议：** 先完成第 1 节 Docker 安装并重启（必要时安装 WSL），再用第 2 节：获取 Dify → 进入 docker 目录 → 复制并修改 .env（端口冲突时必改）→ 执行 `docker compose up -d`。如果你不熟悉镜像、容器、Compose、volume、端口映射，先看 [第 8.1 章 Docker 入门与 Dify 部署排障](8.1-Docker入门与Dify部署常见问题.md)。

**官方文档与资源**：详见 [工具导航与参考资料索引 - 低代码与智能体平台](工具导航与参考资料索引.md#低代码与智能体平台)。

---

## 1、部署 Dify 之前，你需要准备什么

Windows 本地部署 Dify，核心依赖只有两个：

- **Docker Desktop**
- **Dify 项目代码**

为什么一定要 Docker？因为 Dify 不是单一程序，而是一整套协同服务。你启动的不只是一个前端页面，而是一组相互配合的容器，例如：

- Web 前端
- API 服务
- Worker
- 数据库
- Redis
- 向量数据库等

部署主线可以直接概括成一句话：**安装 Docker Desktop -> 获取 Dify 项目 -> 配置 `.env` -> `docker compose up -d` -> 浏览器访问。**

本章只讲 Dify 的最小部署流程。Docker 通用概念、常用命令，以及部署后的排障、升级、数据库连接统一放在 [第 8.1 章 Docker 入门与 Dify 部署排障](8.1-Docker入门与Dify部署常见问题.md)。

## 2、Docker Desktop 安装

### 2.1 下载安装包

官网：https://www.docker.com/

方式 1：选择版本下载：

![获取 Dify 项目代码的课程资料界面](images/7/7-3-1-1.png)

方式 2：从网盘资料里获取：

![课程资料中提供的 Docker Desktop 安装包界面](images/7/7-2-1-2.png)

### 2.2 开始安装

点击确认即可：

![在 Dify docker 目录中复制 .env.example 的界面](images/7/7-3-2-1.png)

等待安装完成：

![修改 Dify .env 端口配置的界面](images/7/7-3-2-2.png)

### 2.3 重启电脑

![在终端中进入 Dify docker 目录的界面](images/7/7-4-1-1.png)

也可以关闭窗口，稍后自行重启。

### 2.4 首次启动 Docker Desktop

重启后通常会自动弹出服务协议页面，点击接受：

![执行 docker compose up -d 启动 Dify 的界面](images/7/7-4-2-1.png)

完成安装：

![Dify 首次安装完成后的命令行界面](images/7/7-4-2-2.png)

允许系统控制：

![再次执行 docker compose up -d 启动已有服务的界面](images/7/7-4-2-3.png)

如无特殊需要，可以不登录：

![Docker Desktop 跳过登录的界面](images/7/7-2-4-4.png)

继续跳过引导：

![Docker Desktop 跳过新手引导的界面](images/7/7-2-4-5.png)

> 如果 Windows 提示需要安装 WSL（Windows Subsystem for Linux），直接按提示完成即可。在入门阶段，不必把 WSL 理解得太深，只需要知道：**Docker Desktop 在 Windows 上通常需要借助 WSL 2 提供 Linux 运行环境。**

### 2.5 验证 Docker 是否安装成功

按 `Win + R` 打开运行，输入 `cmd` 并回车：

![Dify 本地部署完成后的主界面](images/7/7-4-3-2.png)

执行：

```bash
docker --version
docker compose version
```

若能正常输出版本信息，说明 Docker Desktop 已经可用。

![Dify 首次访问时设置管理员账户的界面](images/7/7-4-3-1.png)

## 3、获取 Dify 项目并完成最小配置

### 3.1 获取 Dify 代码

GitHub 地址：

https://github.com/langgenius/Dify

也可以从课程网盘资料中获取：

![获取 Dify 项目代码的课程资料界面](images/7/7-3-1-1.png)

这一步只需要记住一件事：

> **你后面真正操作的目录，不是仓库根目录，而是仓库里的 `docker` 目录。**

### 3.2 复制 `.env.example` 为 `.env`

下面的操作，官方文档里也有说明：

https://docs.dify.ai/zh-hans/getting-started/install-self-hosted/docker-compose

进入 Dify 仓库下的 `docker` 目录，将 `.env.example` 复制并重命名为 `.env`：

![在 Dify docker 目录中复制 .env.example 的界面](images/7/7-3-2-1.png)

然后按需修改 `.env` 中的配置，例如端口。

![修改 Dify .env 端口配置的界面](images/7/7-3-2-2.png)

这一小步非常关键，因为 `.env` 决定了部署时使用的运行参数。第一次部署最常改的通常只有一项：

- **端口**

如果本机 `80` 端口被其他程序占用了，就改成 `8100`、`8080` 或其他未被占用端口。

> 可以这样理解：`.env` 像这套部署环境的“总开关配置文件”。Docker / Compose / 数据卷的通用关系和 Dify 场景排障见 [第 8.1 章](8.1-Docker入门与Dify部署常见问题.md)。

## 4、启动 Dify

### 4.1 打开终端并进入 docker 目录

以下操作可在 Windows 命令行（cmd）、PowerShell 或 Docker Desktop 自带终端里完成。

进入 Dify 仓库下的 `docker` 目录：

![在终端中进入 Dify docker 目录的界面](images/7/7-4-1-1.png)

### 4.2 执行启动命令

执行：

```bash
docker compose up -d
```

![执行 docker compose up -d 启动 Dify 的界面](images/7/7-4-2-1.png)

首次启动时，它会自动拉取镜像、创建容器、初始化服务，这个过程可能比较慢。

安装完成后：

![Dify 首次安装完成后的命令行界面](images/7/7-4-2-2.png)

再次执行 `docker compose up -d` 时，通常就是启动已有服务：

![再次执行 docker compose up -d 启动已有服务的界面](images/7/7-4-2-3.png)

在 Docker Desktop 的 Containers 页面中可以看到当前运行的容器：

![Docker Desktop 中查看 Dify 容器运行状态的界面](images/7/7-4-2-4.png)

### 4.3 浏览器访问

浏览器访问：

- 默认端口：`http://localhost`
- 如果你把端口改成了 `8100`：`http://localhost:8100`

首次访问需要设置管理员用户名与密码：

![Dify 首次访问时设置管理员账户的界面](images/7/7-4-3-1.png)

进入后，平台的使用方式就和 Dify 云平台基本一致了：

![Dify 本地部署完成后的主界面](images/7/7-4-3-2.png)

---

**章节思考题：**

1. 为什么 Dify 本地部署里，`.env` 往往是最容易被忽略但很关键的文件？

   **答案：** 因为 `.env` 决定了数据库、缓存、端口、密钥、域名等核心运行参数，很多“服务起不来”“页面打不开”“模型接不上”的问题，根源都在这里。它不是附属文件，而是部署配置中心。

2. 如果浏览器访问不到 Dify，除了看页面本身，还应该先检查什么？

   **答案：** 先检查容器是否真的启动、端口是否正确映射、本机防火墙或代理是否拦截，以及 `docker compose ps` 和日志里有没有明显报错。页面访问不到，往往不是浏览器问题，而是底层服务没起来。

3. `docker compose up -d` 这条命令在部署流程里到底在做什么？

   **答案：** 它会根据 `docker-compose.yaml` 把需要的多个服务一起创建并在后台启动，例如 Web、API、数据库、Redis 等。也就是说，它不是单纯“运行一个程序”，而是在拉起一整套协同服务。

4. 如果你要教一个完全没做过部署的同学把 Dify 跑起来，你会把整条流程拆成哪几个步骤？

   **答案：** 我会拆成五步：先准备 Docker 环境；再拿到 Dify 项目并进入正确目录；然后配置 `.env`；接着执行 `docker compose up -d` 启动服务；最后用浏览器访问并结合日志做首次验证。

5. 遇到镜像拉取失败、端口冲突、容器未启动时，你会怎样用“环境 -> 配置 -> 容器 -> 访问”这条顺序排查？

   **答案：** 我会先看环境层是否能正常联网和拉镜像，再看配置层有没有端口或 `.env` 问题，然后看容器层是否启动成功、日志有没有报错，最后再看访问层是否被端口、防火墙或代理拦住。这个顺序能避免一上来就只盯着网页现象。

**本章小结：**

- **部署主线**：Dify 的 Windows 本地部署可以浓缩成一条很清晰的链路：**装 Docker -> 获取 Dify -> 配置 `.env` -> `docker compose up -d` -> 浏览器访问**。
- **排障重点**：最常见的问题通常不是 Dify 本身，而是 Docker / WSL、端口占用、镜像拉取和配置文件处理。
- **课程位置**：这章的意义不只是把 Dify 跑起来，更是帮你为后面的私有化、企业部署和 Docker 排障打基础。
- 从掌握结果看，学完本章后，你至少应该：能在 Windows 上正确安装 Docker Desktop，并知道 WSL 提示出现时该怎么处理；能完成 Dify 的最小本地部署：获取代码、修改 `.env`、执行 `docker compose up -d`、浏览器访问；能理解端口冲突、镜像拉取失败、容器状态异常这些常见部署问题的大致排查方向。

**建议下一步：** 如果你想补 Docker 基础，或者要排 Dify 部署、升级、数据库连接相关问题，看 [第 8.1 章 Docker 入门与 Dify 部署排障](8.1-Docker入门与Dify部署常见问题.md)；如果你要走更完整的企业部署链路，则进入 [第 8 章 企业级大模型部署](8-企业级大模型部署.md)。
