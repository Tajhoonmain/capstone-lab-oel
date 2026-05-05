import asyncio
from mcp_project.app.multi_agent_graph import multi_agent_app
from langchain_core.messages import HumanMessage


async def debug_astream():
    inputs = {"messages": [HumanMessage(content="Hello")], "sender": "user"}
    config = {"configurable": {"thread_id": "test_id_123"}}

    try:
        async for event in multi_agent_app.astream(inputs, config, stream_mode="updates"):
            print(event)
    except Exception as e:
        print(f"Exception caught: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_astream())
