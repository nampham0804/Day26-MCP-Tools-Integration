# 02 — MCP Basics (Server + Client)

Cùng tool `get_weather`, nhưng giờ tách ra **MCP server độc lập**. Server tự công bố
tool qua giao thức MCP; bất kỳ client nào (Claude Code, Cursor, hoặc `weather_client.py`)
cũng cắm vào dùng được — không cần biết code bên trong.

```
weather_client.py                       weather_server.py
┌─────────────┐    giao thức MCP    ┌─────────────────┐
│  list_tools │ ──────────────────▶ │ @mcp.tool()     │
│  call_tool  │ ◀────────────────── │ get_weather()   │
└─────────────┘     stdio           └─────────────────┘
```

## Cách chạy (không cần API key)

```bash
pip install -r ../requirements.txt
python weather_client.py     # client tự khởi động weather_server.py
```

Kết quả mong đợi:

```
Tools server cung cấp:
  - get_weather: Lấy thời tiết hiện tại của một thành phố.

call_tool get_weather(city='Hanoi'):
  -> Hanoi: 29°C, trời mưa

call_tool get_weather(city='Danang'):
  -> Danang: 30°C, nhiều mây

call_tool get_weather(city='Haiphong'):
  -> Haiphong: 33°C, mưa rào
```

## Files

| File | Mô tả |
|---|---|
| `weather_server.py` | MCP server — `@mcp.tool()` tự sinh schema từ type hints + docstring |
| `weather_client.py` | MCP client — `list_tools` + `call_tool` qua stdio transport |

## Khác biệt so với Function Calling thuần

| | 01-function-calling | 02-mcp-basics |
|---|---|---|
| Khai báo schema | Viết tay `FunctionDeclaration` | `@mcp.tool()` tự sinh |
| Nơi thực thi tool | Trong app gọi model | Trong MCP server riêng |
| Khám phá tool | Hard-code danh sách | `list_tools()` tại runtime |
| Dùng lại ở app khác | Copy code | Cắm thêm client |

## Đăng ký server với AI client

**Claude Code** (làm 1 lần, dùng mãi):

```bash
claude mcp add weather -- python /đường/dẫn/tới/weather_server.py
```

**Gemini CLI**:

```bash
# Thêm vào ~/.gemini/settings.json
"mcpServers": {
  "weather": {
    "command": "python",
    "args": ["/đường/dẫn/tới/weather_server.py"]
  }
}
```

Bước tiếp theo: [03-production/](../03-production/) — Auth, Tool Registry, Versioning.
