"""
LangChain 1.x 中使用 Pydantic 进行数据验证的示例大全

Pydantic 在 LangChain 中的三个典型用途：
  1. model.with_structured_output(Schema) —— 结构化输出的 schema
  2. @tool(args_schema=Schema)            —— 工具入参的自动校验
  3. PydanticOutputParser                 —— 输出解析与校验

本文件系统演示 Pydantic v2 的绝大部分数据验证用法（LangChain 1.x 基于 Pydantic v2）。
第 1~11 节全部离线可运行（不需要 API Key）；第 12~13 节是 LangChain 集成，需要 OPENAI_API_KEY。

运行前准备：pip install -U pydantic langchain langchain-openai
"""

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PositiveInt,
    SecretStr,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)


def banner(title: str) -> None:
    print(f"\n{'=' * 22} {title} {'=' * 22}")


# ---------------------------------------------------------------------------
# 1. 基础字段：类型注解 + Field(description / default / default_factory)
#    description 对 LangChain 尤其重要——它会进入发给模型的 JSON Schema，指导模型填字段
# ---------------------------------------------------------------------------
class BasicUser(BaseModel):
    name: str = Field(description="用户姓名")
    age: int = Field(default=18, description="年龄")           # 默认值
    tags: list[str] = Field(default_factory=list)              # 可变默认值必须用 default_factory
    created_at: datetime = Field(default_factory=datetime.now)


def demo_basic_fields() -> None:
    user = BasicUser(name="张三")
    print(user)
    print("JSON Schema（with_structured_output 会把它发给模型）：")
    print(BasicUser.model_json_schema())


# ---------------------------------------------------------------------------
# 2. 字段约束：数值范围、字符串长度、正则；校验失败抛 ValidationError
# ---------------------------------------------------------------------------
class Product(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0, description="价格，必须大于 0")   # gt >, ge >=, lt <, le <=
    discount: float = Field(default=1.0, ge=0, le=1)
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$", description="货号，格式如 ABC-1234")
    stock: PositiveInt = 0                                       # pydantic 内置约束类型


def demo_constraints() -> None:
    ok = Product(name="机械键盘", price=299.0, sku="KEY-0001")
    print(ok)

    try:
        Product(name="x", price=-5, sku="bad-format")
    except ValidationError as e:
        print("校验失败，错误明细：")
        for err in e.errors():
            print(f"  字段 {err['loc']}: {err['msg']} (type={err['type']})")


# ---------------------------------------------------------------------------
# 3. 可选值 / 联合类型 / Literal / Enum
# ---------------------------------------------------------------------------
class Sentiment(str, Enum):          # str 型 Enum：序列化友好，适合让模型做枚举输出
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Review(BaseModel):
    text: str
    sentiment: Sentiment
    score: Optional[float] = None                      # 可选字段（可为 None）
    language: Literal["zh", "en", "ja"] = "zh"         # 限定取值集合
    reply: Union[str, None] = None                     # Union 类型
    extra: Union[dict, list, None] = None


def demo_optional_union() -> None:
    r = Review(text="很好用", sentiment="positive")    # 字符串自动转换为 Enum
    print(r)
    print("sentiment 类型：", type(r.sentiment))


# ---------------------------------------------------------------------------
# 4. 嵌套模型与集合类型：dict 会自动递归转换为子模型
# ---------------------------------------------------------------------------
class Address(BaseModel):
    city: str
    street: str
    zipcode: str = Field(pattern=r"^\d{6}$")


class Order(BaseModel):
    order_id: str
    address: Address                                   # 嵌套模型
    items: list[Product]                               # 模型列表
    quantities: dict[str, int] = Field(default_factory=dict)
    coupon: Optional[tuple[str, float]] = None


def demo_nested() -> None:
    order = Order(
        order_id="ORD-1",
        address={"city": "北京", "street": "长安街", "zipcode": "100000"},  # dict 自动转 Address
        items=[{"name": "鼠标", "price": 99, "sku": "MOU-0001"}],           # dict 自动转 Product
        quantities={"MOU-0001": 2},
    )
    print(order)
    print("嵌套访问：", order.address.city, order.items[0].price)


# ---------------------------------------------------------------------------
# 5. 特殊类型：日期、URL、敏感字符串
# ---------------------------------------------------------------------------
class Article(BaseModel):
    title: str
    publish_date: date                                 # "2026-07-17" 自动解析为 date
    source: Optional[HttpUrl] = None                   # 校验 URL 合法性（pydantic 内置）
    api_key: Optional[SecretStr] = None                # 打印时脱敏，取值用 get_secret_value()
    # email: Optional[EmailStr] = None                 # 需额外安装 pip install email-validator


def demo_special_types() -> None:
    a = Article(
        title="LangChain 1.x 发布",
        publish_date="2026-07-17",
        source="https://example.com/news/1",
        api_key="sk-super-secret",
    )
    print(a)                                           # api_key 显示为 **********
    print("publish_date 类型：", type(a.publish_date))
    print("取出密钥：", a.api_key.get_secret_value())


# ---------------------------------------------------------------------------
# 6. field_validator：单字段自定义校验 / 预处理
#    mode="after"（默认）在校验后处理；mode="before" 拿到原始输入，可做类型归一化
# ---------------------------------------------------------------------------
class Username(BaseModel):
    name: str
    password: str

    @field_validator("name")
    @classmethod
    def name_must_be_alpha(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("姓名只能包含字母")
        return v

    @field_validator("password", mode="before")
    @classmethod
    def password_to_str(cls, v):
        return str(v)                                  # int 输入先归一化成 str 再校验


def demo_field_validator() -> None:
    print(Username(name="zhangsan", password=123456))
    try:
        Username(name="zhangsan123", password="x")
    except ValidationError as e:
        print("校验失败：", e.errors()[0]["msg"])


# ---------------------------------------------------------------------------
# 7. model_validator：跨字段联合校验
# ---------------------------------------------------------------------------
class DateRange(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def check_range(self):
        if self.end < self.start:
            raise ValueError("end 不能早于 start")
        return self


def demo_model_validator() -> None:
    print(DateRange(start="2026-01-01", end="2026-12-31"))
    try:
        DateRange(start="2026-12-31", end="2026-01-01")
    except ValidationError as e:
        print("跨字段校验失败：", e.errors()[0]["msg"])


# ---------------------------------------------------------------------------
# 8. computed_field：派生字段（参与序列化输出，不参与输入校验）
# ---------------------------------------------------------------------------
class Rectangle(BaseModel):
    width: float = Field(gt=0)
    height: float = Field(gt=0)

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height


def demo_computed_field() -> None:
    r = Rectangle(width=3, height=4)
    print("area =", r.area)
    print("model_dump 包含计算字段：", r.model_dump())


# ---------------------------------------------------------------------------
# 9. model_config：模型级配置
#    extra="forbid" 禁止多余字段（对接 LLM 输出时很有用，防止模型乱加字段）
# ---------------------------------------------------------------------------
class StrictConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",                # 多余字段直接报错（默认 ignore）
        str_strip_whitespace=True,     # 字符串自动去首尾空白
    )

    city: str


def demo_model_config() -> None:
    print(StrictConfig(city="  北京  "))
    try:
        StrictConfig(city="北京", hallucinated_field="模型多输出的字段")
    except ValidationError as e:
        print("多余字段被拒绝：", e.errors()[0]["msg"])


# ---------------------------------------------------------------------------
# 10. 别名：alias / populate_by_name，对接外部 camelCase 风格 JSON
# ---------------------------------------------------------------------------
class ApiResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)   # 同时允许用字段名填充

    user_name: str = Field(alias="userName")           # 输入/输出默认用 userName
    age: int = 0


def demo_alias() -> None:
    r = ApiResponse.model_validate({"userName": "张三", "age": 20})
    print(r.user_name)
    print("按别名序列化：", r.model_dump(by_alias=True))
    print("按字段名序列化：", r.model_dump())


# ---------------------------------------------------------------------------
# 11. 序列化与反序列化全家桶
# ---------------------------------------------------------------------------
def demo_serialization() -> None:
    user = BasicUser(name="李四", age=30, tags=["admin"])

    d = user.model_dump()                              # -> dict
    j = user.model_dump_json()                         # -> JSON 字符串
    print(d)
    print(j)

    u2 = BasicUser.model_validate(d)                   # dict -> 模型（带校验）
    u3 = BasicUser.model_validate_json(j)              # JSON 字符串 -> 模型（带校验）
    print("两种反序列化结果相等：", u2 == u3)

    # 常用选项：排除 None / 只导出部分字段
    print(user.model_dump(exclude_none=True))
    print(user.model_dump(include={"name", "age"}))


# ---------------------------------------------------------------------------
# 12. LangChain 集成一：with_structured_output
#     所有校验规则（约束、validator、extra="forbid"）都会作用于模型输出
# ---------------------------------------------------------------------------
class PersonInfo(BaseModel):
    """从文本中提取的人物信息。"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="人物姓名")
    age: int = Field(ge=0, le=150, description="年龄，0-150")
    occupation: Optional[str] = Field(default=None, description="职业，未知则为 null")

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()


def demo_langchain_structured_output() -> None:
    from langchain.chat_models import init_chat_model

    model = init_chat_model("openai:gpt-4o-mini", temperature=0)
    structured = model.with_structured_output(PersonInfo)

    result = structured.invoke("马斯克今年50多岁，是特斯拉的CEO。")
    print(type(result), result)                        # 返回校验通过的 PersonInfo 实例


# ---------------------------------------------------------------------------
# 13. LangChain 集成二：@tool(args_schema=...) 用 Pydantic 校验工具入参
#     模型给出的工具参数会先过 Pydantic 校验，不合法直接抛 ValidationError
# ---------------------------------------------------------------------------
def demo_langchain_tool_args() -> None:
    from langchain.tools import tool

    class SearchInput(BaseModel):
        query: str = Field(min_length=1, description="搜索关键词")
        max_results: int = Field(default=5, ge=1, le=50, description="返回条数，1-50")

    @tool(args_schema=SearchInput)
    def search(query: str, max_results: int = 5) -> str:
        """搜索互联网上的信息。"""
        return f"搜索「{query}」，返回前 {max_results} 条结果。"

    # 合法调用
    print(search.invoke({"query": "LangChain", "max_results": 3}))
    # 非法调用：max_results 超出范围，被 Pydantic 校验拦截
    try:
        search.invoke({"query": "LangChain", "max_results": 999})
    except ValidationError as e:
        print("工具入参被拦截：", e.errors()[0]["msg"])


if __name__ == "__main__":
    # 第 1~11 节：纯 Pydantic，离线可运行
    banner("1. 基础字段")
    demo_basic_fields()
    banner("2. 字段约束")
    demo_constraints()
    banner("3. Optional / Union / Literal / Enum")
    demo_optional_union()
    banner("4. 嵌套模型与集合")
    demo_nested()
    banner("5. 特殊类型")
    demo_special_types()
    banner("6. field_validator 单字段校验")
    demo_field_validator()
    banner("7. model_validator 跨字段校验")
    demo_model_validator()
    banner("8. computed_field 计算字段")
    demo_computed_field()
    banner("9. model_config 模型配置")
    demo_model_config()
    banner("10. 别名")
    demo_alias()
    banner("11. 序列化 / 反序列化")
    demo_serialization()

    # 第 12~13 节：LangChain 集成，需要 OPENAI_API_KEY，取消注释即可运行
    # banner("12. LangChain: with_structured_output")
    # demo_langchain_structured_output()
    # banner("13. LangChain: 工具入参校验")
    # demo_langchain_tool_args()
