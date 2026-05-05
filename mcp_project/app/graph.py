import os
from typing import Annotated, Sequence, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from mcp_project.app.tools import tools
from dotenv import load_dotenv

load_dotenv()

# 1. Define the Graph State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# 2. Define the Agent Node
def call_model(state: AgentState):
    messages = state['messages']
    model = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# 3. Custom Tool Node (Handles tool execution manually to avoid import errors)
def tool_node(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    
    # Create a dictionary of tools by name for easy lookup
    tools_by_name = {tool.name: tool for tool in tools}
    
    outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Invoke the selected tool
        if tool_name in tools_by_name:
            observation = tools_by_name[tool_name].invoke(tool_args)
        else:
            observation = f"Tool {tool_name} not found."
            
        outputs.append(ToolMessage(
            content=str(observation),
            tool_call_id=tool_call["id"],
        ))
        
    return {"messages": outputs}

# 4. Define the Router Logic
def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

# 5. Initialize the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

workflow.add_edge("tools", "agent")

app = workflow.compile()
