"""
【案例】PydanticOutputParser：用 Pydantic 模型定义输出结构并校验

对应教程章节：第 14 章 - 输出解析器 → 3、结构化输出（TypedDict / Pydantic / Annotated）

知识点速览：
一、PydanticOutputParser 和 JsonOutputParser 的区别？
  - JsonOutputParser：把模型文本解析成「任意」JSON（dict/list），或可绑一个 Pydantic 模型约束形状。
  - PydanticOutputParser：**专门**配合 Pydantic 模型，解析结果会转成** Pydantic 实例**，并可利用 Pydantic 的校验（如字段类型、validator），不合格会抛错。

二、本案例流程：用 Pydantic 定义 Product（name、category、description），其中 description 用 field_validator 校验长度 ≥ 10 → 用 PydanticOutputParser(pydantic_object=Product) 创建解析器 → 用 get_format_instructions() 得到格式说明并拼进 Prompt → 模型返回后 parser.invoke(result) 得到 Product 对象。
  - 适合：需要强类型、需要在校验失败时明确报错的场景。
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, Field, field_validator

load_dotenv(encoding="utf-8")


class Product(BaseModel):
    """产品信息：名称、类别、简介。简介长度需 ≥ 10，由下方 validator 校验。"""

    name: str = Field(description="产品名称")
    category: str = Field(description="产品类别")
    description: str = Field(description="产品简介")

    @field_validator("description")
    def validate_description(cls, value):
        """Pydantic 校验器：description 长度必须 ≥ 10，否则抛 ValueError。"""
        if len(value) < 10:
            raise ValueError("产品简介长度必须大于等于10")
        return value


# 创建 Pydantic 输出解析器：解析结果会转成 Product 实例并做校验
parser = PydanticOutputParser(pydantic_object=Product)

# 生成「格式说明」字符串，拼进 Prompt，引导模型按 Product 的字段输出 JSON
format_instructions = parser.get_format_instructions()

# 在 system 里放入 {format_instructions}，human 里放 {topic}
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个AI助手，你只能输出结构化的json数据\n{format_instructions}"),
        ("human", "请你输出标题为：{topic}的新闻内容"),
    ]
)

prompt = prompt_template.format_messages(
    topic="华为Mate X7", format_instructions=format_instructions
)
logger.info(prompt)

model = init_chat_model(
    model="grok-4.5",
    model_provider="openai",  # OpenAI 兼容接口
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://www.micuapi.ai/v1",
)

result = model.invoke(prompt)
logger.info(f"模型原始输出:\n{result.content}")

# 解析：把 result 转成 Product 实例，若格式或校验不通过会抛错
response = parser.invoke(result)
logger.info(f"解析后的结构化结果:\n{response}")
logger.info(f"结果类型: {type(response)}")  # <class 'Product'>

print("*" * 80)

model_with_structured_output = model.with_structured_output(Product)
resp = model_with_structured_output.invoke(
    [
        ("system", "你是一个AI助手，你只能输出结构化的json数据\n"),
        ("human", "请你输出标题为：GPT5.6的新闻内容"),
    ]
)
print(resp)

"""
【输出示例】
2026-02-27 15:02:47.018 | INFO     | __main__:<module>:53 - [SystemMessage(content='你是一个AI助手，你只能输出结构化的json数据\nThe output should be formatted as a JSON instance that conforms to the JSON schema below.\n\nAs an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}\nthe object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\nHere is the output schema:\n```\n{"description": "产品信息：名称、类别、简介。简介长度需 ≥ 10，由下方 validator 校验。", "properties": {"name": {"description": "产品名称", "title": "Name", "type": "string"}, "category": {"description": "产品类别", "title": "Category", "type": "string"}, "description": {"description": "产品简介", "title": "Description", "type": "string"}}, "required": ["name", "category", "description"]}\n```', additional_kwargs={}, response_metadata={}), HumanMessage(content='请你输出标题为：华为Mate X7的新闻内容', additional_kwargs={}, response_metadata={})]
2026-02-27 15:02:51.175 | INFO     | __main__:<module>:63 - 模型原始输出:
{"name": "华为Mate X7", "category": "智能手机", "description": "华为Mate X7是一款全新折叠屏旗舰手机，搭载麒麟9010芯片与HarmonyOS 4.2系统，配备8英寸内屏与6.5英寸外屏，支持5G网络与超高速充电技术。"}
2026-02-27 15:02:51.175 | INFO     | __main__:<module>:67 - 解析后的结构化结果:
name='华为Mate X7' category='智能手机' description='华为Mate X7是一款全新折叠屏旗舰手机，搭载麒麟9010芯片与HarmonyOS 4.2系统，配备8英寸内屏与6.5英寸外屏，支持5G网络与超高速充电技术。'
2026-02-27 15:02:51.175 | INFO     | __main__:<module>:68 - 结果类型: <class '__main__.Product'>
"""
