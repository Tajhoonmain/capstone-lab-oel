import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure we can import from mcp_project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from mcp_project.client_bridge import run_query

app = FastAPI(title="MCP Academic Demo API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask(request: QueryRequest):
    """
    Bridge endpoint translating HTTP to MCP protocol calls.
    """
    print(f"\n--- Request Received: {request.query} ---")
    
    try:
        response_data = await run_query(request.query)
        
        print("Returning response to frontend")
        return response_data
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Default port 8000 as expected by frontend
    uvicorn.run(app, host="0.0.0.0", port=8000)
