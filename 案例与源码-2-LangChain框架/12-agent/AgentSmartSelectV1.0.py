"""
【案例】多工具并行调用与聚合回答（V1.0：create_agent 一步创建 + 结构化输出）

对应教程章节：第 21 章 - Agent 智能体 → 4、Agent 工作原理（V1.0）

知识点速览：
- V1.0 与 V0.3 对比：不再手写 PromptTemplate、create_tool_calling_agent、AgentExecutor，改为
  create_agent(model, tools, system_prompt, response_format=...) 一步得到可调用的 Agent，对应教程「4、Agent 工作原理（V1.0）」。
- 结构化输出：通过 response_format 指定 TypedDict（如 WeatherCompareOutput），Agent 的返回中会包含
  structured_response 字段，便于程序化处理（如比温度、写结论），而不必从自然语言里再解析。
- 本文件重点演示 `create_agent` 最常见的 4 个输入：`model / tools / system_prompt / response_format`。
  教程里还补充了 `checkpointer / middleware` 这两个更偏工程化的扩展点，但这里不作为主线展开。
- 调用方式：当前示例用 `agent.invoke(...)` 直接看最终结果；如果真实项目里想看中间进展，通常还会配合
  `stream()`，如果想做短期记忆，则会进一步引入 `checkpointer + thread_id`。
"""

import os
import json
import httpx
from pathlib import Path
from typing_extensions import (
    TypedDict,
)  # Python < 3.12 下 Pydantic 要求用 typing_extensions.TypedDict

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# .env 在项目根目录，从任意子目录运行脚本时都从根目录加载
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


@tool
def get_weather(loc: str) -> str:
    """
    查询即时天气函数
    :param loc: 城市英文名，如 Beijing、Shanghai。
    :return: OpenWeather API 返回的天气信息（JSON 字符串）。
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": loc,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric",
        "lang": "zh_cn",
    }
    response = httpx.get(url, params=params, timeout=30)
    data = response.json()
    return json.dumps(data, ensure_ascii=False)


# 定义结构化输出：Agent 最终回答会按此结构填充，便于代码中直接取字段
class WeatherCompareOutput(TypedDict):
    beijing_temp: float
    shanghai_temp: float
    hotter_city: str
    summary: str


model = ChatOpenAI(
    model="grok-4.5",
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://www.micuapi.ai/v1",
)

# V1.0 一步创建 Agent：模型、工具、系统提示、输出格式一次传入
# 如果后面还要扩展短期记忆或拦截控制，通常会继续给 create_agent 传 checkpointer / middleware
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt=(
        "你是天气助手。"
        "当用户询问多个城市天气时，"
        "你需要分别调用工具获取数据，并进行比较分析。"
    ),
    response_format=WeatherCompareOutput,
)

# 调用 Agent，返回结果中包含 messages 与 structured_response（若指定了 response_format）
# 这里先用 invoke 看最终结果；如需观察中间步骤，可在工程里改为 stream()
result = agent.invoke({"input": "请问今天北京和上海的天气怎么样，哪个城市更热？"})
print(result)
print()
print(json.dumps(result["structured_response"], ensure_ascii=False, indent=2))

"""
【输出示例】
{'messages': [AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 38, 'prompt_tokens': 302, 'total_tokens': 340, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-69aa32a9-b752-9356-b407-b45224e3e061', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019ce60c-54cb-75b2-9350-738e1bc5d2b1-0', tool_calls=[{'name': 'get_weather', 'args': {'loc': 'Beijing'}, 'id': 'call_b3c5a5cf5cca4a68ae5e24', 'type': 'tool_call'}, {'name': 'get_weather', 'args': {'loc': 'Shanghai'}, 'id': 'call_6f49e29c6bdb4aec9e6806', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 302, 'output_tokens': 38, 'total_tokens': 340, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}), ToolMessage(content='{"coord": {"lon": 116.3972, "lat": 39.9075}, "weather": [{"id": 804, "main": "Clouds", "description": "阴，多云", "icon": "04d"}], "base": "stations", "main": {"temp": 10.49, "feels_like": 8.51, "temp_min": 10.49, "temp_max": 10.49, "pressure": 1024, "humidity": 35, "sea_level": 1024, "grnd_level": 1019}, "visibility": 10000, "wind": {"speed": 0.49, "deg": 203, "gust": 0.67}, "clouds": {"all": 100}, "dt": 1773385877, "sys": {"country": "CN", "sunrise": 1773354606, "sunset": 1773397087}, "timezone": 28800, "id": 1816670, "name": "Beijing", "cod": 200}', name='get_weather', id='c6d0dda4-dfff-4378-b007-dadb456cadd6', tool_call_id='call_b3c5a5cf5cca4a68ae5e24'), ToolMessage(content='{"coord": {"lon": 121.4581, "lat": 31.2222}, "weather": [{"id": 800, "main": "Clear", "description": "晴", "icon": "01d"}], "base": "stations", "main": {"temp": 15.34, "feels_like": 13.5, "temp_min": 15.34, "temp_max": 15.34, "pressure": 1027, "humidity": 22, "sea_level": 1027, "grnd_level": 1026}, "visibility": 10000, "wind": {"speed": 3.06, "deg": 84, "gust": 2.32}, "clouds": {"all": 0}, "dt": 1773385631, "sys": {"country": "CN", "sunrise": 1773353249, "sunset": 1773396016}, "timezone": 28800, "id": 1796236, "name": "Shanghai", "cod": 200}', name='get_weather', id='60d4a27a-e01e-4c56-921f-975fc620ffe6', tool_call_id='call_6f49e29c6bdb4aec9e6806'), AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 71, 'prompt_tokens': 949, 'total_tokens': 1020, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-080e0e74-3d6d-9fa9-95f8-f6d1070fcc3b', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019ce60c-5e67-7f30-b4a2-abd5c6faf4fb-0', tool_calls=[{'name': 'WeatherCompareOutput', 'args': {'beijing_temp': 10.49, 'shanghai_temp': 15.34, 'hotter_city': 'Shanghai', 'summary': '上海比北京暖和约4.85°C，且天气晴朗，而北京多云。'}, 'id': 'call_e41163c0bf134d8f97eace', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 949, 'output_tokens': 71, 'total_tokens': 1020, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}), ToolMessage(content="Returning structured response: {'beijing_temp': 10.49, 'shanghai_temp': 15.34, 'hotter_city': 'Shanghai', 'summary': '上海比北京暖和约4.85°C，且天气晴朗，而北京多云。'}", name='WeatherCompareOutput', id='4293a8f2-8e2f-4bcf-a9ff-6d5733cab9aa', tool_call_id='call_e41163c0bf134d8f97eace')], 'structured_response': {'beijing_temp': 10.49, 'shanghai_temp': 15.34, 'hotter_city': 'Shanghai', 'summary': '上海比北京暖和约4.85°C，且天气晴朗，而北京多云。'}}
"""

# {
#   "beijing_temp": 10.49,
#   "shanghai_temp": 15.34,
#   "hotter_city": "Shanghai",
#   "summary": "上海比北京暖和约4.85°C，且天气晴朗，而北京多云。"
# }
