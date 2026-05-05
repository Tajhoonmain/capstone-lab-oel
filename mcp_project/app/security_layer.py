import os
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()


# --- 1. State Definition ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_safe: bool  # Flag to determine if we should route to the agent


# --- 2. Security Guardrail Node ---
def guardrail_node(state: AgentState):
    messages = state["messages"]
    user_query = messages[-1].content.lower()

    print(f"\n[SECURITY SHIELD] Analyzing Query: '{user_query}'...")

    # Very simple keyword-based heuristic (In production, this would be a classification LLM or LLM-Guard)
    # We block anything explicitly trying to jailbreak or asking non-academic topics.
    forbidden_phrases = ["forget previous", "ignore all", "act like", "hack", "bypass", "joke", "recipe", "weather"]
    academic_keywords = ["gpa", "course", "grade", "probation", "exam", "student", "credit", "semester", "drop"]

    # 1. Check for jailbreak attempts
    for phrase in forbidden_phrases:
        if phrase in user_query:
            print("[SECURITY SHIELD] BLOCK: Malicious prompt detected!")
            return {
                "messages": [
                    AIMessage(content="Security Violation: I am an Academic Advisor AI. I cannot process this request.")
                ],
                "is_safe": False,
            }

    # 2. Check for out-of-domain topics (If it doesn't contain academic keywords)
    # Note: This is a strict heuristic for demonstration purposes.
    is_academic = any(word in user_query for word in academic_keywords)
    if not is_academic:
        print("[SECURITY SHIELD] BLOCK: Out-of-domain topic detected!")
        return {
            "messages": [
                AIMessage(
                    content="Out of Bounds: I am strictly an Academic Advisor. I can only assist with grades, courses, and university policies."
                )
            ],
            "is_safe": False,
        }

    print("[SECURITY SHIELD] PASS: Query is safe and academic.")
    return {"is_safe": True}


# --- 3. Mock Agent Node (Simulating our actual agent) ---
def dummy_agent_node(state: AgentState):
    print("[AGENT] Processing safe query...")
    return {"messages": [AIMessage(content="I am processing your academic request safely!")]}


# --- 4. Routing Logic ---
def security_router(state: AgentState) -> Literal["agent", "__end__"]:
    # If the guardrail flagged it, skip the agent and end immediately
    if state.get("is_safe") == False:
        return "__end__"
    return "agent"


# --- 5. Build Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("agent", dummy_agent_node)

workflow.set_entry_point("guardrail")
workflow.add_conditional_edges("guardrail", security_router)
workflow.add_edge("agent", END)

secure_app = workflow.compile()
