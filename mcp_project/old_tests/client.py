import asyncio
import os
import sys
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    print("--- MCP Project Demonstration ---")

    # Path to server script
    server_path = os.path.abspath("server.py")

    # Task 2: Connection Initialization
    # Using StdioServerParameters which is REQUIRED by stdio_client
    server_params = StdioServerParameters(command=sys.executable, args=["-u", server_path], env=os.environ.copy())

    print(f"[Client] Connecting to MCP Server via stdio...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Task 2: Establish connection
                await session.initialize()
                print("[Pipeline] Connection: SUCCESS (Handshake complete)")

                # Task 2: Tool Discovery
                tools = await session.list_tools()
                print(f"[Discovery] Discovered {len(tools.tools)} tools on server.")
                for tool in tools.tools:
                    print(f" - {tool.name}: {tool.description}")

                # Task 2: Model Decision & Context Separation
                # Simulated query: "Calculate my GPA for grades A, B, A"
                print("\n[Model] Reasoning: User query requires GPA calculation.")
                print("[Execution] Calling 'calculate_gpa' tool via MCP...")

                # Task 2: Tool Invocation via protocol
                response = await session.call_tool("calculate_gpa", arguments={"grades": ["A", "B", "A"]})

                # Task 2: Structured Output Handling
                if response.content:
                    print(f"[Result] Server Response: {response.content[0].text}")

                print("\n--- Project Demonstrated Successfully ---")

    except Exception as e:
        import traceback

        print(f"\n--- ERROR ---")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
