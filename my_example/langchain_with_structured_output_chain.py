"""
LangChain 1.x：with_structured_output 在 Runnable Chain 中的用法

核心概念：
  model.with_structured_output(Schema) 返回的本身就是一个 Runnable，
  输入与 model 相同（prompt 渲染后的消息），输出是解析好的 Pydantic 对象。

  因此在 prompt | model | parser 中，它整体替换掉 model | parser 这一段：

      chain = prompt | model.with_structured_output(Schema)

  —— 不再需要 parser，结构化解析已在 with_structured_output 内部完成。

运行前准备：
  pip install -U langchain langchain-openai pydantic
  并设置环境变量 OPENAI_API_KEY
"""

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. 定义输出结构：Pydantic 模型，Field 的 description 会指导模型填充字段
# ---------------------------------------------------------------------------
class Joke(BaseModel):
    """一个笑话的结构化表示。"""

    setup: str = Field(description="笑话的铺垫")
    punchline: str = Field(description="笑话的笑点/包袱")
    rating: int = Field(description="好笑程度，1 到 10 分")


model = init_chat_model("openai:gpt-4o-mini", temperature=0)

# ---------------------------------------------------------------------------
# 2. with_structured_output 返回一个 Runnable：
#    输入 = model 的输入，输出 = Joke 实例（不是 AIMessage，不是字符串）
# ---------------------------------------------------------------------------
structured_model = model.with_structured_output(Joke)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个讲笑话的助手。"),
        ("human", "讲一个关于{topic}的笑话。"),
    ]
)

# ---------------------------------------------------------------------------
# 3. 放进 chain：取代原来 parser 的位置
#    对比旧写法：prompt | model | PydanticOutputParser(pydantic_object=Joke)
#    新写法：    prompt | structured_model
# ---------------------------------------------------------------------------
chain = prompt | structured_model


def demo_basic() -> None:
    result = chain.invoke({"topic": "程序员"})

    # result 直接就是 Joke 对象，可以访问字段，也有类型检查
    print(type(result))  # <class 'Joke'>
    print(result)
    print(f"铺垫：{result.setup}")
    print(f"包袱：{result.punchline}")
    print(f"评分：{result.rating}/10")


# ---------------------------------------------------------------------------
# 4. chain 还可以继续往后接：下游步骤收到的就是 Pydantic 对象
#    （普通 Python 函数在 | 组合中会自动包装成 RunnableLambda）
# ---------------------------------------------------------------------------
def format_joke(joke: Joke) -> str:
    return f"{joke.setup} —— {joke.punchline}（好笑程度 {joke.rating}/10）"


full_chain = prompt | structured_model | format_joke


def demo_downstream() -> None:
    text = full_chain.invoke({"topic": "咖啡"})
    print(text)  # 输出格式化后的字符串


# ---------------------------------------------------------------------------
# 补充说明
# ---------------------------------------------------------------------------
# * 批量 / 流式等 Runnable 协议同样适用：
#     chain.batch([{"topic": "猫"}, {"topic": "狗"}])
#
# * 若需要容错（模型输出解析失败时不直接抛异常），可用 include_raw=True：
#     model.with_structured_output(Joke, include_raw=True)
#   但此时输出变成 {"raw": AIMessage, "parsed": Joke | None, "parsing_error": ...}
#   的字典，下游步骤的输入契约随之改变，需要自行取 ["parsed"]。
#
# * 不支持 function calling 的模型可指定 method="json_mode"：
#     model.with_structured_output(Joke, method="json_mode")


if __name__ == "__main__":
    print("=" * 20, "基础用法", "=" * 20)
    demo_basic()
    print("=" * 20, "继续接下游步骤", "=" * 20)
    demo_downstream()
