import os
from typing import Annotated, Sequence, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

load_dotenv()

# --- 1. Define High-Risk Tool ---
@tool
def drop_course_tool(course_code: str, reason: str):
    """
    HIGH RISK ACTION: Drops a course from the student's current registration.
    Only use this if the student explicitly asks to drop a course.
    """
    return f"SUCCESS: Course {course_code} has been dropped for reason: {reason}."

tools = [drop_course_tool]
tools_dict = {t.name: t for t in tools}

# --- 2. Define State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# --- 3. Define Nodes ---
def call_model(state: AgentState):
    messages = state['messages']
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def tool_node(state: AgentState):
    last_message = state['messages'][-1]
    outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in tools_dict:
            observation = tools_dict[tool_name].invoke(tool_call["args"])
        else:
            observation = "Tool not found."
        outputs.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": outputs}

def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

# --- 4. Build Graph with Checkpointer and Breakpoints ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

import sqlite3

# Initialize Checkpointer (Local database for this lab)
conn = sqlite3.connect("checkpoint_db.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Compile with interrupt_before the tools node (Human in the Loop)
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["tools"]
)
