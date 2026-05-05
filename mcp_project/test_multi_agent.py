from mcp_project.app.multi_agent_graph import multi_agent_app
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()


def test_collaboration(query: str):
    print(f"\n=============================================")
    print(f"USER QUERY: {query}")
    print(f"=============================================")

    inputs = {"messages": [HumanMessage(content=query)], "sender": "user"}

    for output in multi_agent_app.stream(inputs):
        for key, value in output.items():
            print(f"\n[{key.upper()}] says:")
            if "messages" in value:
                last_msg = value["messages"][-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    print(f"-> Calling Tool: {last_msg.tool_calls[0]['name']}")
                else:
                    print(last_msg.content)


if __name__ == "__main__":
    # Test: The user asks a question that requires BOTH agents to work.
    # Agent A (Researcher) must find the GPA policy in the handbook.
    # Agent B (Advisor) must calculate the actual GPA using the tool and format the email.

    test_collaboration(
        "I got an A, C, and F in my courses. First, look up the minimum GPA required to graduate. "
        "Then, calculate my current GPA. Finally, tell me if I am eligible to graduate."
    )
