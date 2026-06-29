# 01 — Function Calling thuần (Google Gemini SDK)

Tool `get_weather` được **định nghĩa schema thủ công** và **thực thi ngay trong app**.
Model chỉ quyết định gọi tool nào — app mới là nơi chạy.

```
User hỏi  →  Model quyết định gọi get_weather(city="Hà Nội")
                     │
                     ▼
              App TỰ THỰC THI hàm get_weather
                     │
                     ▼
              Model tổng hợp câu trả lời
```

## Cách chạy

```bash
pip install -r ../requirements.txt
export GEMINI_API_KEY=...
python weather_function_calling.py
```

## File

| File | Mô tả |
|---|---|
| `weather_function_calling.py` | Định nghĩa schema, thực thi tool, gọi model Gemini, xử lý vòng lặp function calling |

## Luồng hoạt động

1. App định nghĩa `FunctionDeclaration` với schema viết tay (tên, tham số, kiểu)
2. App gửi prompt + danh sách tool tới Gemini
3. Model trả về `function_calls` — yêu cầu gọi `get_weather`
4. App **tự chạy** hàm `get_weather()` và đưa kết quả trả lại model
5. Model tổng hợp câu trả lời cuối cho user

## Nhược điểm

- Schema viết tay, dễ lệch với implementation
- Tool gắn chặt trong app — muốn dùng lại ở app khác phải copy cả schema lẫn hàm
- Mỗi model provider (OpenAI, Anthropic, Google) có format khác nhau

Bước tiếp theo: [02-mcp-basics/](../02-mcp-basics/) — tách tool ra MCP server độc lập.
