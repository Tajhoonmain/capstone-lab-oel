import os
import time
from typing import Annotated, Sequence, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from mcp_project.app.tools import calculate_gpa_tool, check_exam_schedule_tool, academic_policy_lookup_tool
from mcp_project.app.agents_config import RESEARCHER_PROMPT, ADVISOR_PROMPT
from dotenv import load_dotenv

load_dotenv("mcp_project/.env")

MODEL_NAME = "gemini-2.0-flash"

def invoke_with_retry(model, messages, max_retries=3):
    """Invoke a model with automatic retry on 429 rate limit errors."""
    for attempt in range(max_retries):
        try:
            return model.invoke(messages)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 60 * (attempt + 1)  # wait 60s, 120s, 180s
                print(f"[RATE LIMIT] Quota hit. Retrying in {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Model failed after {max_retries} retries due to rate limiting.")

# Split the tools based on personas
researcher_tools = [academic_policy_lookup_tool]
advisor_tools = [calculate_gpa_tool, check_exam_schedule_tool]

# Create dictionaries for fast lookup
researcher_tools_dict = {t.name: t for t in researcher_tools}
advisor_tools_dict = {t.name: t for t in advisor_tools}

# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    sender: str # Keeps track of who is currently active

# 2. Agent Nodes
def researcher_node(state: AgentState):
    messages = state['messages']
    
    # Prepend the system prompt if not present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=RESEARCHER_PROMPT)] + list(messages)
        
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    ).bind_tools(researcher_tools)
    
    response = invoke_with_retry(model, messages)
    return {"messages": [response], "sender": "researcher"}

def advisor_node(state: AgentState):
    messages = state['messages']
    
    # We add the Advisor's system prompt to the context
    context_msgs = [SystemMessage(content=ADVISOR_PROMPT)] + list(messages)
    
    # Gemini requires alternating roles. Since the Researcher's last message was an AIMessage,
    # we simulate the system asking the Advisor to take over.
    context_msgs.append(HumanMessage(content="[SYSTEM]: The Researcher has finished gathering information. Advisor, please formulate the final response for the student using your tools if needed."))
    
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    ).bind_tools(advisor_tools)
    
    response = invoke_with_retry(model, context_msgs)
    return {"messages": [response], "sender": "advisor"}

# 3. Tool Nodes (Custom implementations to avoid LangGraph version issues)
def researcher_tools_node(state: AgentState):
    last_message = state['messages'][-1]
    outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in researcher_tools_dict:
            observation = researcher_tools_dict[tool_name].invoke(tool_call["args"])
        else:
            observation = "Error: Tool not allowed for Researcher."
        outputs.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": outputs}

def advisor_tools_node(state: AgentState):
    last_message = state['messages'][-1]
    outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name in advisor_tools_dict:
            observation = advisor_tools_dict[tool_name].invoke(tool_call["args"])
        else:
            observation = "Error: Tool not allowed for Advisor."
        outputs.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": outputs}

# 4. Routing Logic
def researcher_router(state: AgentState):
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "researcher_tools"
    # When Researcher finishes its thought/output, pass to Advisor
    return "advisor"

def advisor_router(state: AgentState):
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "advisor_tools"
    # When Advisor finishes, end the graph
    return END

# 5. Build Graph
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("advisor", advisor_node)
workflow.add_node("researcher_tools", researcher_tools_node)
workflow.add_node("advisor_tools", advisor_tools_node)

# Set entry point
workflow.set_entry_point("researcher")

# Add Researcher edges
workflow.add_conditional_edges("researcher", researcher_router)
workflow.add_edge("researcher_tools", "researcher")

# Add Advisor edges
workflow.add_conditional_edges("advisor", advisor_router)
workflow.add_edge("advisor_tools", "advisor")

from langgraph.checkpoint.memory import MemorySaver

# Compile with Checkpointer
memory = MemorySaver()
multi_agent_app = workflow.compile(checkpointer=memory)
