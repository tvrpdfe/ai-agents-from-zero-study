"""
【案例】基于 mcp.json + LangChain 1.x Agent 的 MCP 客户端（LLM + MCP 工具）

对应教程章节：
- 第 20 章 - MCP 模型上下文协议 → 6、案例实战：本地 MCP 天气服务与客户端
- 第 21 章 - Agent 智能体 → 4、Agent 工作原理（V1.0） / 5、实操与案例（5.4 Agent + MCP）

知识点速览：
- 与同目录 McpClientAgent.py（classic / 0.x 路线）对照：MCP 配置加载、MultiServerMCPClient、
  get_tools 完全相同；差异只在「把工具交给 Agent」这一段。
- 1.x 路线：`await client.get_tools()` 之后交给 `langchain.agents.create_agent`，
  再配合 `ainvoke()` / `astream()` 使用，不再手写 ChatPromptTemplate、
  create_tool_calling_agent、AgentExecutor，也不再需要 agent_scratchpad。
- 输入/输出形态变化：
  - 输入：`{"messages": [{"role": "user", "content": ...}]}`（不再用 `{"input": ...}`）
  - 输出：从 `result["messages"][-1].content` 取最终回答（不再用 `result["output"]`）
- MCP 工具多为异步，本文件统一用 `await agent.ainvoke(...)`。
- 依赖：pip install langchain langchain-mcp-adapters langchain-openai loguru；
  部分适配器要求 Python 3.12 及以下。需配置环境变量 DEEPSEEK_API_KEY（兼容旧名 deepseek-api）。
- 运行前：先启动本目录 McpServerWeatherByFastMCP.py；fetch 服务用当前 conda 的
  `python -m mcp_server_fetch`（需 pip install mcp-server-fetch）。Windows + conda + Git Bash
  下若 SSL_CERT_FILE 指向错误路径，本文件会自动修正。
"""

import asyncio
import json
import os
import shutil
from pathlib import Path

from loguru import logger

# 默认 mcp.json 路径（与本文件同目录）
_MCP_JSON_PATH = Path(__file__).resolve().parent / "mcp.json"


def _fix_ssl_cert_file() -> None:
    """
    修复 conda 在 Git Bash 下可能设置的错误 SSL_CERT_FILE。

    Windows conda 的 openssl_activate.sh 会把证书指到
    $CONDA_PREFIX/ssl/cacert.pem，但实际文件在
    $CONDA_PREFIX/Library/ssl/cacert.pem。路径无效时 httpx/mcp
    会在创建 SSL 上下文阶段直接 FileNotFoundError。
    """
    ssl_cert = os.environ.get("SSL_CERT_FILE")
    if ssl_cert and Path(ssl_cert).is_file():
        return

    candidates: list[Path] = []
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        prefix = Path(conda_prefix)
        candidates.extend(
            [
                prefix / "Library" / "ssl" / "cacert.pem",
                prefix / "ssl" / "cacert.pem",
            ]
        )
    try:
        import certifi

        candidates.append(Path(certifi.where()))
    except ImportError:
        pass

    for candidate in candidates:
        if candidate.is_file():
            os.environ["SSL_CERT_FILE"] = str(candidate)
            logger.info(f"已修正 SSL_CERT_FILE -> {candidate}")
            return

    if ssl_cert:
        # 无效路径会让 httpx 直接崩溃；清掉后回退到系统/certifi 默认逻辑
        logger.warning(f"SSL_CERT_FILE 无效且未找到可用证书，已清除: {ssl_cert}")
        os.environ.pop("SSL_CERT_FILE", None)


def _resolve_deepseek_api_key() -> str | None:
    """兼容 DEEPSEEK_API_KEY 与历史命名 deepseek-api。"""
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("deepseek-api")


def load_servers(file_path: str | Path | None = None) -> dict:
    """
    加载 MCP 服务器配置。
    :param file_path: 配置文件路径，默认使用同目录下的 mcp.json
    :return: 完整配置字典，如 {"mcpServers": {"weather": {...}, "fetch": {...}}}

    这里读取的是“客户端如何连接服务”的约定配置，而不是协议本体。
    """
    path = Path(file_path) if file_path else _MCP_JSON_PATH
    if not path.exists():
        logger.warning(f"未找到 mcp 配置文件: {path}")
        return {"mcpServers": {}}
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logger.info(
        f"已加载 mcp 配置: {path}，共 {len(config.get('mcpServers', {}))} 个服务"
    )
    return config


def _preflight_servers(servers: dict) -> dict:
    """
    启动前做轻量检查，过滤明显不可用的服务，并给出可操作的提示。
    返回仍可尝试连接的服务子集。
    """
    usable: dict = {}
    for name, conf in servers.items():
        if not isinstance(conf, dict):
            logger.warning(f"跳过服务 {name}: 配置不是对象")
            continue

        transport = (conf.get("transport") or "").lower()
        if transport == "stdio" or "command" in conf:
            command = conf.get("command")
            if not command:
                logger.warning(f"跳过服务 {name}: stdio 配置缺少 command")
                continue
            if shutil.which(command) is None:
                logger.warning(
                    f"跳过服务 {name}: 找不到命令 '{command}'。"
                    f"请确认已激活 conda 环境，或从 mcp.json 中暂时移除该服务。"
                )
                continue
            # python -m xxx：额外检查模块是否已安装，避免起进程后才失败
            args = conf.get("args") or []
            if (
                command in {"python", "python3", "python.exe"}
                and len(args) >= 2
                and args[0] == "-m"
            ):
                module_name = args[1]
                import importlib.util

                if importlib.util.find_spec(module_name) is None:
                    logger.warning(
                        f"跳过服务 {name}: 当前环境未安装模块 '{module_name}'。"
                        f"可在已激活的 conda 环境中执行: pip install {module_name.replace('_', '-')}"
                    )
                    continue
        elif transport in {"sse", "http", "streamable_http", "streamable-http"} or "url" in conf:
            url = conf.get("url")
            if not url:
                logger.warning(f"跳过服务 {name}: 缺少 url")
                continue
        else:
            logger.warning(
                f"服务 {name} 未识别 transport={transport!r}，仍尝试连接"
            )

        usable[name] = conf

    return usable


async def _load_tools_best_effort(servers: dict):
    """
    逐个服务拉取工具。MultiServerMCPClient.get_tools() 默认 gather 全部服务，
    任一失败就会整体抛错；这里改成 best-effort，方便本地只起了部分服务时仍可演示。
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    tools = []
    failed: list[str] = []
    for name, conf in servers.items():
        try:
            client = MultiServerMCPClient(connections={name: conf})
            server_tools = await client.get_tools()
            tools.extend(server_tools)
            logger.info(
                f"服务 {name} 已连接，工具: {[t.name for t in server_tools]}"
            )
        except Exception as exc:
            failed.append(name)
            hint = ""
            if conf.get("transport") == "sse" or conf.get("url"):
                hint = (
                    f" 请确认已先启动对应 MCP 服务（例如本目录的 "
                    f"McpServerWeatherByFastMCP.py），且可访问 {conf.get('url')}。"
                )
            logger.error(f"连接 MCP 服务 {name} 失败: {exc}.{hint}")

    if failed and not tools:
        raise RuntimeError(
            "所有 MCP 服务均连接失败: "
            + ", ".join(failed)
            + "。请检查：1) weather 服务是否已启动；"
            "2) stdio 命令/模块是否可用（如 python -m mcp_server_fetch）；"
            "3) SSL_CERT_FILE 是否指向存在的证书文件。"
        )
    if failed:
        logger.warning(f"以下服务连接失败，已忽略: {failed}")
    return tools


def _final_answer(messages) -> str:
    """从 1.x Agent 返回的 messages 中取出最终文本回答。"""
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", last)
    if isinstance(content, list):
        # 部分模型会返回多段 content block
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content) if content is not None else ""


async def run_chat_loop(config_path: str | Path | None = None) -> None:
    """
    启动并运行一个基于 MCP 工具的聊天 Agent 循环（LangChain 1.x / create_agent）。

    该函数会：1）加载 MCP 服务器配置；2）初始化 MCP 客户端并获取工具；
    3）用 create_agent 创建基于 DeepSeek 的 Agent；4）启动命令行聊天循环。
    """
    _fix_ssl_cert_file()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    try:
        import importlib.util

        if importlib.util.find_spec("langchain_mcp_adapters") is None:
            raise ImportError("No module named 'langchain_mcp_adapters'")
        if importlib.util.find_spec("langchain.agents") is None:
            raise ImportError("No module named 'langchain.agents'")
    except ImportError as e:
        logger.error(
            "请先安装依赖: pip install langchain langchain-mcp-adapters langchain-openai"
            "（部分环境需 Python 3.12 及以下）"
        )
        raise e

    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI

    config = load_servers(config_path)
    servers = config.get("mcpServers", {})
    if not servers:
        logger.warning("mcp.json 中未配置任何服务，无法获取 MCP 工具")
        return

    servers = _preflight_servers(servers)
    if not servers:
        logger.error(
            "没有可连接的 MCP 服务。常见原因：\n"
            "  - fetch 需要当前 conda 环境已安装 mcp-server-fetch"
            "（pip install mcp-server-fetch）\n"
            "  - weather 需要先运行 McpServerWeatherByFastMCP.py\n"
            "请修正 mcp.json 或补齐运行环境后重试。"
        )
        return

    # 按服务 best-effort 获取工具，避免单个服务失败拖垮整个 Agent
    tools = await _load_tools_best_effort(servers)
    if not tools:
        logger.warning(
            "未从 MCP 服务获取到任何工具，请确认服务已启动且 mcp.json 配置正确"
        )
        return

    logger.info(f"已获取 {len(tools)} 个 MCP 工具: {[t.name for t in tools]}")

    api_key = _resolve_deepseek_api_key()
    if not api_key:
        logger.error(
            "未找到 DeepSeek API Key。请设置环境变量 DEEPSEEK_API_KEY"
            "（兼容旧名 deepseek-api）后重试。"
        )
        return

    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    # 1.x：一步创建 Agent；system_prompt 替代 ChatPromptTemplate + agent_scratchpad
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="你是一个有用的助手，需要使用提供的工具来完成用户请求。",
    )

    logger.info("\n MCP Agent (LangChain 1.x) 已启动，请先输入一个提问给(LLM+MCP)，输入 'quit' 退出")

    while True:
        try:
            user_input = input("\n您: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                logger.info("已退出")
                break

            # 1.x 标准输入是 messages；MCP 工具多为 async，用 ainvoke
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )
            output = _final_answer(result.get("messages", []))
            print(f"\nAgent: {output}")
        except KeyboardInterrupt:
            logger.info("已退出")
            break


def main() -> None:
    asyncio.run(run_chat_loop())


if __name__ == "__main__":
    main()
