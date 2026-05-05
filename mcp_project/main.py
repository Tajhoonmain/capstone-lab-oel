from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
import asyncio

# Import our Multi-Agent Graph
from mcp_project.app.multi_agent_graph import multi_agent_app

app = FastAPI(
    title="Academic Advisor API",
    description="Agentic LangGraph Backend for Student Advising",
    version="1.0.0"
)

# --- Define Request Payload ---
class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_session"

# --- Streaming Endpoint ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Accepts a query and streams the thought process of the Multi-Agent system 
    back to the client in real-time using Server-Sent Events (SSE).
    """
    
    async def event_generator():
        # Prepare the input for the LangGraph
        inputs = {"messages": [HumanMessage(content=request.query)], "sender": "user"}
        config = {"configurable": {"thread_id": request.thread_id}}
        
        try:
            # Stream events from the graph asynchronously
            async for event in multi_agent_app.astream(inputs, config, stream_mode="updates"):
                # Iterate through the nodes that produced updates
                for node_name, node_state in event.items():
                    if "messages" in node_state:
                        last_msg = node_state["messages"][-1]
                        
                        # 1. Handle Tool Calls
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            tool_name = last_msg.tool_calls[0]['name']
                            payload = json.dumps({"node": node_name, "type": "tool_call", "content": f"Calling tool: {tool_name}..."})
                            yield f"data: {payload}\n\n"
                            
                        # 2. Handle Text Output
                        elif last_msg.content:
                            # Handle both plain string and list-of-dicts content formats
                            raw_content = last_msg.content
                            if isinstance(raw_content, list):
                                # Extract just the plain text blocks, ignore signature/extras
                                text_parts = [block.get("text", "") for block in raw_content if isinstance(block, dict) and block.get("type") == "text"]
                                clean_content = " ".join(text_parts).strip()
                            else:
                                clean_content = str(raw_content)
                            
                            if clean_content:
                                payload = json.dumps({"node": node_name, "type": "message", "content": clean_content})
                                yield f"data: {payload}\n\n"
                            
                # Small async sleep to prevent blocking the event loop
                await asyncio.sleep(0.1)
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            with open("server_error.log", "w") as f:
                import traceback
                f.write(traceback.format_exc())
            yield f"data: [ERROR] {str(e)}\n\n"

    # Return the stream using text/event-stream for SSE
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Simple Health Check ---
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Academic Advisor API is running."}

# To run: uvicorn mcp_project.main:app --reload
