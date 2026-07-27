import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-06-01",          # 支持 tools 的稳定版本
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

# ---------- 1. 定义本地函数（真实业务逻辑） ----------
def extract_student_info(name: str, major: str, school: str, grades: float, club: str):
    """模拟从文本提取信息后的处理，比如存数据库"""
    # 这里你可以做任何你想做的事，我们只简单返回一个确认字符串
    return f"已成功提取学生 {name} 的信息，GPA 为 {grades}"

# ---------- 2. 定义 Tool Schema（给 AI 看的说明书） ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "extract_student_info",
            "description": "从文本中提取学生信息，包括姓名、专业、学校、GPA（数字）和社团",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "学生全名"},
                    "major": {"type": "string", "description": "专业名称"},
                    "school": {"type": "string", "description": "大学名称"},
                    "grades": {"type": "number", "description": "GPA 数值，例如 3.7"},
                    "club": {"type": "string", "description": "主要参与的社团"},
                },
                "required": ["name", "major", "school", "grades", "club"],
            },
        },
    }
]

# ---------- 3. 构建初始消息 ----------
user_query = "Emily Johnson is a sophomore majoring in computer science at Duke University. She has a 3.7 GPA and is in the Chess Club."
messages = [
    {"role": "user", "content": user_query}
]

# ---------- 4. 第一次请求 ----------
print("🔹 第一次请求：发送用户问题 + 工具定义")
first_response = client.chat.completions.create(
    model=deployment,
    messages=messages,
    tools=tools,
    tool_choice="auto",  # 让 AI 自己决定是否调用
)

# 获取助手的回复
assistant_message = first_response.choices[0].message

# ---------- 5. 第一次 append：将助手的回复（可能含 tool_calls）追加到消息历史 ----------
messages.append(assistant_message)   # 这是第一个 append
print("📥 已追加 assistant 消息（含 tool_calls）")

# ---------- 6. 检查 AI 是否要求调用工具 ----------
if assistant_message.tool_calls:
    # 遍历所有工具调用（理论上可能多个，这里只处理第一个）
    for tool_call in assistant_message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        print(f"🔧 AI 请求调用工具: {function_name}，参数: {function_args}")

        # ---------- 7. 执行本地函数，得到结果 ----------
        if function_name == "extract_student_info":
            # 这里调用我们的本地函数
            function_result = extract_student_info(**function_args)
            print(f"✅ 本地函数执行结果: {function_result}")

            # ---------- 8. 第二次 append：将工具执行结果作为 tool 消息追加 ----------
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,   # 必须与 tool_call 的 id 对应
                "content": function_result,
            })
            print("📥 已追加 tool 消息（工具执行结果）")

    # ---------- 9. 第二次请求：带着完整历史再问 AI，让它基于工具结果生成最终回答 ----------
    print("\n🔹 第二次请求：发送完整对话历史（含工具结果）")
    second_response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        # 注意：第二次请求不再提供 tools，因为 AI 已经拿到了结果
    )

    final_answer = second_response.choices[0].message.content
    print("\n📢 AI 最终回复：")
    print(final_answer)

else:
    # 如果 AI 没有调用工具，直接输出它的回复
    print("🤖 AI 直接回复（未调用工具）：")
    print(assistant_message.content)