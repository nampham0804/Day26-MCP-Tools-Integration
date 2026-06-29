"""Minh hoạ FUNCTION CALLING thuần với Anthropic SDK.

Tool `get_weather` được định nghĩa schema thủ công VÀ thực thi ngay trong
chính file app này. Model chỉ QUYẾT ĐỊNH gọi tool nào; app mới là nơi chạy.

Cách chạy:
    pip install -r ../requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    python weather_function_calling.py
"""

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-opus-4-8"

# 1. App tự định nghĩa schema của tool (hard-code trong app)
TOOLS = [
    {
        "name": "get_weather",
        "description": "Lấy thời tiết hiện tại của một thành phố",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Tên thành phố"}
            },
            "required": ["city"],
        },
    }
]


# 2. App tự thực thi tool (ở thực tế sẽ gọi API thời tiết thật)
def get_weather(city: str) -> str:
    fake_db = {
        "Hà Nội": "31°C, trời nắng",
        "Hồ Chí Minh": "33°C, mưa rào",
        "Đà Nẵng": "30°C, nhiều mây",
    }
    return f"{city}: {fake_db.get(city, '28°C, không có dữ liệu chi tiết')}"


def run(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.messages.create(
        model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages
    )

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả lại
    while resp.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": resp.content})

        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                print(f"  [model yêu cầu] {block.name}({block.input})")
                result = get_weather(**block.input)  # <-- app chạy, không phải model
                print(f"  [app thực thi]  -> {result}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages
        )

    # 5. Model tổng hợp câu trả lời cuối
    return "".join(b.text for b in resp.content if b.type == "text")


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
