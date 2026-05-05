import asyncio
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Task 1: Create a standalone MCP server
server = Server("University-Assistant")


@server.list_tools()
async def handle_list_tools():
    """Define structured tools with input schemas."""
    return [
        types.Tool(
            name="calculate_gpa",
            description="Calculate GPA from letter grades.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grades": {"type": "array", "items": {"type": "string", "enum": ["A", "B", "C", "D", "F"]}}
                },
                "required": ["grades"],
            },
        ),
        types.Tool(
            name="check_exam_schedule",
            description="Get exam schedule for a course.",
            inputSchema={
                "type": "object",
                "properties": {"course_code": {"type": "string"}},
                "required": ["course_code"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
    """Execute tools via the MCP protocol."""
    if name == "calculate_gpa":
        grades = arguments.get("grades", [])
        pts = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        gpa = sum(pts.get(g.upper(), 0) for g in grades) / len(grades) if grades else 0.0
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Calculated GPA: {round(gpa, 2)}")], isError=False
        )
    elif name == "check_exam_schedule":
        course = arguments.get("course_code", "").upper()
        schedules = {"AI407": "Monday 2:00 PM - Room 301", "CS101": "Tuesday 10:00 AM - Room 205"}
        time = schedules.get(course, f"No exam schedule found for {course}")
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Exam for {course}: {time}")], isError=False
        )
    else:
        raise ValueError(f"Tool not found: {name}")


async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="University-Assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
