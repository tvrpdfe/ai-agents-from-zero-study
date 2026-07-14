"""
【案例】文本提示词模板：组合多个 PromptTemplate

对应教程章节：第 13 章 - 提示词与消息模板 → 6、文本提示词模板（PromptTemplate）

知识点速览：
- 多个 `PromptTemplate` 可以通过 `+` 组合成一个更长的整体提示，适合把“角色说明、业务规则、当前任务”拆开维护。
- 组合后仍然是新的模板对象，`format(...)` 时需要传入所有占位符变量。
"""

from langchain_core.prompts import PromptTemplate

# ---------- 1. 方式一：一个 from_template 与一段字符串用 + 拼接 ----------
template1 = (
    PromptTemplate.from_template("请用一句话介绍{topic}，要求通俗易懂\n")
    + "内容不超过{length}个字"
)

prompt1 = template1.format(topic="LangChain", length=100)
print(prompt1)

# ---------- 2. 方式二：两个独立模板相加，再一起 format ----------
prompt_a = PromptTemplate.from_template("请用一句话介绍{topic}，要求通俗易懂\n")
prompt_b = PromptTemplate.from_template("内容不超过{length}个字")
prompt_all = prompt_a + prompt_b
prompt2 = prompt_all.format(topic="LangChain", length=200)
print(prompt2)

"""
【输出示例】
请用一句话介绍LangChain，要求通俗易懂
内容不超过100个字
请用一句话介绍LangChain，要求通俗易懂
内容不超过200个字
"""
