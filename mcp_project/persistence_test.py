from mcp_project.app.approval_logic import app
from langchain_core.messages import HumanMessage


def run_persistence_test():
    # Thread ID acts as our User Session ID
    config = {"configurable": {"thread_id": "student_123"}}

    print("\n=== USER: I want to drop course CS101. ===")
    inputs = {"messages": [HumanMessage(content="I want to drop course CS101 because it's too hard.")]}

    # Run the graph until it hits the breakpoint
    for event in app.stream(inputs, config, stream_mode="values"):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print(f"[AGENT PAUSED] Agent wants to call: {last_msg.tool_calls[0]['name']}")
            elif last_msg.type == "ai":
                print(f"[AGENT]: {last_msg.content}")

    # Check if the graph is waiting
    state = app.get_state(config)
    if state.next:
        print("\n[SYSTEM] Execution paused! Waiting for Human-in-the-Loop approval...")
        print(f"Pending tasks: {state.next}")

        user_input = input("Approve the drop course action? (yes/no): ")
        if user_input.lower() == "yes":
            print("\n[SYSTEM] Action approved. Resuming execution...")
            # Resume execution with None (tells graph to continue from current state)
            for event in app.stream(None, config, stream_mode="values"):
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    if last_msg.type == "ai" and not hasattr(last_msg, "tool_calls"):
                        print(f"[AGENT FINAL]: {last_msg.content}")
        else:
            print("\n[SYSTEM] Action cancelled by user.")

    # Prove that the memory persists in the database
    print("\n=== USER: Wait, what course did I just ask about? ===")
    followup_input = {"messages": [HumanMessage(content="Wait, what course did I just ask about?")]}

    # We use the exact same config/thread_id
    for event in app.stream(followup_input, config, stream_mode="values"):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"[AGENT MEMORY]: {last_msg.content}")


if __name__ == "__main__":
    run_persistence_test()
