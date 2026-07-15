"""
【案例】JsonOutputParser + get_format_instructions()：用格式说明引导模型输出

对应教程章节：第 14 章 - 输出解析器 → 2、常用输出解析器用法

知识点速览：
一、get_format_instructions() 做什么？
  - 返回一段格式说明字符串，描述「希望模型输出成什么样子」（例如 JSON 里有哪些键、类型是什么）。
  - 把这段说明拼进 Prompt（如放在 {format_instructions} 占位符），模型更容易输出可被解析的 JSON，减少格式错误。

二、本案例做法：用 Pydantic 模型 Person 定义「时间、人物、事件」结构 → 用 JsonOutputParser(pydantic_object=Person) 创建解析器 → 用 parser.get_format_instructions() 得到说明 → 把说明拼进 human 消息，再调用模型与解析器。
  - 模型会按 Person 的 schema 生成 JSON；当前 JsonOutputParser 解析结果为 dict（若要 Pydantic 实例与完整校验，见 PydanticOutputParser / StructuredOutput_Pydantic.py）。
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger
from pydantic import BaseModel, Field

load_dotenv(encoding="utf-8")


class Person(BaseModel):
    """定义一条「新闻」的结构：时间、人物、事件。用于约束模型输出的 JSON 形状。"""

    time: str = Field(description="时间")
    person: str = Field(description="人物")
    event: str = Field(description="事件")


# 绑定 Pydantic 模型：主要驱动 get_format_instructions() 的 schema；invoke 后得到 dict
parser = JsonOutputParser(pydantic_object=Person)

# 获取「格式说明」：描述 Person 各字段，便于拼进提示词让模型按此输出
format_instructions = parser.get_format_instructions()
logger.info(f"格式说明:\n{format_instructions}")

# 在 human 消息里加入 {format_instructions}，模型会看到「请按如下格式输出 JSON …」
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个AI助手，你只能输出结构化JSON数据。"),
        ("human", "请生成一个关于{topic}的新闻。{format_instructions}"),
    ]
)

# 填 topic 和 format_instructions，得到消息列表
prompt = chat_prompt.format_messages(
    topic="肯尼迪", format_instructions=format_instructions
)
logger.info(prompt)

model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

result = model.invoke(prompt)
logger.info(f"模型原始输出:\n{result}")

# 用同一解析器解析，得到符合 Person 结构的数据（dict，或可转成 Person 实例）
response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info(f"结果类型: {type(response)}")

"""
【输出示例】
2026-02-27 15:01:43.675 | INFO     | __main__:<module>:47 - [SystemMessage(content='你是一个AI助手，你只能输出结构化JSON数据。', additional_kwargs={}, response_metadata={}), HumanMessage(content='请生成一个关于小米su7跑车的新闻。STRICT OUTPUT FORMAT:\n- Return only the JSON value that conforms to the schema. Do not include any additional text, explanations, headings, or separators.\n- Do not wrap the JSON in Markdown or code fences (no ``` or ```json).\n- Do not prepend or append any text (e.g., do not write "Here is the JSON:").\n- The response must be a single top-level JSON value exactly as required by the schema (object/array/etc.), with no trailing commas or comments.\n\nThe output should be formatted as a JSON instance that conforms to the JSON schema below.\n\nAs an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]} the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\nHere is the output schema (shown in a code block for readability only — do not include any backticks or Markdown in your output):\n```\n{"description": "定义一条「新闻」的结构：时间、人物、事件。用于约束模型输出的 JSON 形状。", "properties": {"time": {"description": "时间", "title": "Time", "type": "string"}, "person": {"description": "人物", "title": "Person", "type": "string"}, "event": {"description": "事件", "title": "Event", "type": "string"}}, "required": ["time", "person", "event"]}\n```', additional_kwargs={}, response_metadata={})]
2026-02-27 15:01:47.540 | INFO     | __main__:<module>:57 - 模型原始输出:
content='{"time": "2024年3月28日", "person": "雷军", "event": "小米正式发布首款高性能纯电动轿车SU7，百公里加速2.78秒，续航达800公里，开启预订后24小时订单突破10万辆"}' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 64, 'prompt_tokens': 385, 'total_tokens': 449, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'qwen-plus', 'system_fingerprint': None, 'id': 'chatcmpl-2ca1b345-6e47-9595-ad8a-37df86762530', 'finish_reason': 'stop', 'logprobs': None} id='lc_run--019c9de7-3f73-7081-bd8c-977d405da6ab-0' tool_calls=[] invalid_tool_calls=[] usage_metadata={'input_tokens': 385, 'output_tokens': 64, 'total_tokens': 449, 'input_token_details': {'cache_read': 0}, 'output_token_details': {}}
2026-02-27 15:01:47.540 | INFO     | __main__:<module>:61 - 解析后的结构化结果:
{'time': '2024年3月28日', 'person': '雷军', 'event': '小米正式发布首款高性能纯电动轿车SU7，百公里加速2.78秒，续航达800公里，开启预订后24小时订单突破10万辆'}
2026-02-27 15:01:47.540 | INFO     | __main__:<module>:62 - 结果类型: <class 'dict'>
"""
