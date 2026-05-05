from mcp_project.app.multi_agent_graph import multi_agent_app
from langchain_core.messages import HumanMessage
import uuid


def run_trace():
    print("Sending query to LangGraph...")
    print("If your LANGCHAIN_API_KEY is correct, this execution will automatically be logged to LangSmith!")

    # Generate a unique thread ID so you can easily find it in LangSmith
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    query = "Look up the BS AI degree plan and tell me my GPA if I got an A in CS101, B in MT101, and C in EE101."

    inputs = {"messages": [HumanMessage(content=query)], "sender": "user"}

    for event in multi_agent_app.stream(inputs, config, stream_mode="updates"):
        for node_name, state in event.items():
            if "messages" in state:
                last_msg = state["messages"][-1]
                if last_msg.content:
                    print(f"[{node_name.upper()}]: {last_msg.content}")

    print(f"\n✅ Execution Complete!")
    print(f"Go to https://smith.langchain.com/ and look for project: academic_advisor_v1")
    print(f"Your trace thread_id is: {thread_id}")


if __name__ == "__main__":
    run_trace()
