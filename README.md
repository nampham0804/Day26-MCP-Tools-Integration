# Phân biệt MCP và Function Calling

Đây là hai khái niệm hay bị nhầm lẫn nhưng thực ra ở **hai tầng khác nhau**, và **bổ sung cho nhau** chứ không thay thế.

## Định nghĩa ngắn gọn

**Function Calling** là một *khả năng của model* (capability). Model được huấn luyện để khi bạn đưa cho nó danh sách các "công cụ" (kèm schema mô tả tham số), nó có thể tự quyết định gọi công cụ nào và sinh ra JSON tham số phù hợp. Bản thân model **không chạy** function — nó chỉ nói "hãy gọi `get_weather(city='Hanoi')`". Code của bạn mới là người thực thi.

**MCP (Model Context Protocol)** là một *giao thức chuẩn* (protocol) — giống như USB-C hay HTTP cho thế giới AI. Nó định nghĩa cách một **MCP Client** (như Claude Code, Claude Desktop) kết nối tới các **MCP Server** để khám phá và sử dụng tools, resources, prompts một cách thống nhất.

## So sánh trực tiếp

| Tiêu chí | Function Calling | MCP |
|---|---|---|
| **Bản chất** | Khả năng của LLM | Giao thức giao tiếp client–server |
| **Tầng** | Tầng model | Tầng hạ tầng/tích hợp |
| **Ai định nghĩa tool?** | Bạn hard-code trong từng app | Server tự công bố (self-describe) tool |
| **Tái sử dụng** | Phải viết lại cho mỗi app/model | Viết 1 lần, mọi MCP client dùng được |
| **Thực thi** | App của bạn tự chạy | MCP Server chạy, client điều phối |
| **Tính chuẩn hóa** | Mỗi nhà cung cấp 1 kiểu (OpenAI, Anthropic khác nhau) | Một chuẩn chung do Anthropic đề xuất |
| **Phạm vi** | Chỉ "gọi hàm" | Tools + Resources + Prompts |

## Quan hệ giữa chúng

Điểm quan trọng nhất: **MCP dùng Function Calling bên dưới**. Chúng không loại trừ nhau.

```
User hỏi
   │
   ▼
LLM (dùng Function Calling để quyết định gọi tool nào)
   │
   ▼
MCP Client  ──[giao thức MCP]──►  MCP Server (thực thi tool thật)
   │                                   │
   ◄───────────── kết quả ─────────────┘
   ▼
LLM tổng hợp câu trả lời
```

## Ví dụ minh họa

**Chỉ Function Calling (cách cũ):** Bạn viết app, định nghĩa tool `get_weather` ngay trong code, tự gọi API thời tiết, tự xử lý. Nếu muốn dùng tool này ở app khác → copy/viết lại.

**Với MCP:** Bạn viết một **weather MCP server** một lần. Sau đó Claude Desktop, Claude Code, Cursor... đều cắm vào dùng được mà không cần sửa code. Server tự "khai báo" nó có tool gì.

## Khi nào dùng cái nào?

- **Function Calling thuần**: app đơn giản, tool gắn chặt với 1 ứng dụng, không cần chia sẻ.
- **MCP**: muốn tool/tích hợp dùng lại được trên nhiều AI client, muốn tách biệt logic tool khỏi app, hoặc xây hệ sinh thái tích hợp (DB, file, API nội bộ...).

## Minh hoạ bằng mã nguồn

Cùng một tool `get_weather`, dưới đây là hai cách triển khai để thấy rõ sự khác biệt.

### Cách 1 — Function Calling thuần (Anthropic SDK)

Tool được **định nghĩa và thực thi ngay trong app**. Model chỉ quyết định gọi tool nào, app tự chạy và đưa kết quả trở lại.

```python
# pip install anthropic
import anthropic

client = anthropic.Anthropic()

# 1. App tự định nghĩa schema của tool (hard-code trong app)
tools = [
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

# 2. App tự thực thi tool
def get_weather(city: str) -> str:
    # Ở đây thường gọi API thời tiết thật; demo trả về cứng
    return f"{city}: 31°C, trời nắng"

messages = [{"role": "user", "content": "Thời tiết Hà Nội thế nào?"}]

# 3. Gọi model — model QUYẾT ĐỊNH gọi tool nào, KHÔNG tự chạy
resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

# 4. App đọc yêu cầu gọi tool và TỰ THỰC THI
if resp.stop_reason == "tool_use":
    tool_use = next(b for b in resp.content if b.type == "tool_use")
    result = get_weather(**tool_use.input)  # <-- app chạy, không phải model

    messages.append({"role": "assistant", "content": resp.content})
    messages.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": result,
        }],
    })

    # 5. Gọi lại model để nó tổng hợp câu trả lời cuối
    final = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )
    print(final.content[0].text)
```

> Nhược điểm: nếu muốn dùng `get_weather` ở một app khác, bạn phải copy lại cả schema lẫn hàm thực thi.

### Cách 2 — MCP (server tự công bố tool, mọi client dùng chung)

Tool được tách ra **một MCP server độc lập**. Server tự "khai báo" nó có tool gì; bất kỳ MCP client nào (Claude Code, Claude Desktop, Cursor...) cũng cắm vào dùng được mà không cần biết code bên trong.

**Server** — `weather_server.py`:

```python
# pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

# Chỉ cần decorator — schema được TỰ ĐỘNG sinh ra từ type hints + docstring
@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: 31°C, trời nắng"

if __name__ == "__main__":
    mcp.run()  # chạy server qua stdio
```

**Client** — kết nối tới server và để model gọi tool qua giao thức MCP:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["weather_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Client KHÁM PHÁ tool mà server công bố (không hard-code)
            tools = await session.list_tools()
            print("Tools server cung cấp:", [t.name for t in tools.tools])

            # 2. Client gọi tool — SERVER thực thi rồi trả kết quả về qua MCP
            result = await session.call_tool("get_weather", {"city": "Hà Nội"})
            print("Kết quả:", result.content[0].text)

asyncio.run(main())
```

**Đăng ký server với Claude Code** (làm 1 lần, dùng mãi):

```bash
claude mcp add weather -- python /đường/dẫn/weather_server.py
```

Sau bước này, Claude tự `list_tools` để biết server có `get_weather`, rồi dùng **chính cơ chế Function Calling** để quyết định khi nào gọi — bạn không phải viết thêm dòng code tích hợp nào.

### Điểm khác biệt rút ra từ code

| | Function Calling thuần | MCP |
|---|---|---|
| Khai báo schema | Tự viết tay trong app | `@mcp.tool()` tự sinh từ type hints |
| Nơi thực thi tool | Trong app gọi model | Trong MCP server riêng |
| Khám phá tool | Hard-code danh sách `tools` | `session.list_tools()` tại runtime |
| Dùng lại ở app khác | Copy code | Cắm thêm client, không sửa server |
| Vai trò Function Calling | Là toàn bộ cơ chế | Là lớp model bên trong MCP |

---

**Tóm lại bằng một câu:** Function Calling là *cơ chế model gọi công cụ*; MCP là *chuẩn để kết nối model với các công cụ đó* — và MCP thực chất dùng Function Calling làm nền tảng để hoạt động.
