import asyncio
import os
import sys
import traceback
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    print("================================================")
    print("      MCP PROJECT INDEPENDENT DEMONSTRATION     ")
    print("================================================")

    server_path = os.path.abspath("server.py")

    # Task 2: Connection Initialization Pipeline
    server_params = StdioServerParameters(command=sys.executable, args=["-u", server_path], env=os.environ.copy())

    try:
        print(f"[Pipeline] Connecting to MCP Server via Stdio...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Essential Step: Initialization (Task 2)
                await session.initialize()
                print("[Pipeline] Connection Status: INITIALIZED & READY")

                # Task 2: Tool Discovery Demonstration
                print("\n[Task 2: Discovery] Querying server for available tools...")
                result = await session.list_tools()

                # Handle ListToolsResult which contains a .tools list
                tools = getattr(result, "tools", [])
                print(f"-> Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"   {i}. {tool.name.upper()}: {tool.description}")

                # Task 2: Execution Layer Demonstration
                # Scenario A: Tool 1 - GPA Calculation
                print("\n[Task 2: Execution] Scenario: User query 'Calculate my GPA for A, B, A'")
                print("-> Invoking 'calculate_gpa' tool through MCP protocol...")
                gpa_res = await session.call_tool("calculate_gpa", arguments={"grades": ["A", "B", "A"]})

                # Handling structured output (Task 1/2)
                if hasattr(gpa_res, "content") and gpa_res.content:
                    print(f"-> [Result] Server Response: {gpa_res.content[0].text}")
                else:
                    print(f"-> [Result] Raw Response: {gpa_res}")

                # Scenario B: Tool 2 - Exam Schedule
                print("\n[Task 2: Execution] Scenario: User query 'When is my AI407 exam?'")
                print("-> Invoking 'check_exam_schedule' tool through MCP protocol...")
                exam_res = await session.call_tool("check_exam_schedule", arguments={"course_code": "AI407"})

                if hasattr(exam_res, "content") and exam_res.content:
                    print(f"-> [Result] Server Response: {exam_res.content[0].text}")
                else:
                    print(f"-> [Result] Raw Response: {exam_res}")

                print("\n================================================")
                print("        DEMONSTRATION COMPLETED SUCCESSFULLY    ")
                print("================================================")

    except Exception as e:
        print("\n[!] CRITICAL ERROR During Demonstration:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
