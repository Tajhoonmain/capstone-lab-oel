"""
Production-ready Flask API for MCP Academic Assistant.
Deployed on Render with environment variable support.
"""
import sys
import os
import json
import subprocess
import traceback
import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import time
import random

app = Flask(__name__)

# Production configuration
app.secret_key = os.environ.get('SECRET_KEY', 'mcp-academic-demo-secret-key-2024')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# CORS configuration - allow Render frontend in production
if FLASK_ENV == 'production':
    CORS_origins = ["https://your-app-name.onrender.com"]
else:
    CORS_origins = ["http://localhost:5173", "http://localhost:5174"]

CORS(app, origins=CORS_origins)

# Path to the MCP worker script
MCP_WORKER = os.path.join(os.path.dirname(os.path.abspath(__name__)), "mcp_project", "_mcp_worker.py")

# In-memory session storage (in production, use Redis or database)
user_sessions = {}

# Error handling and retry configuration
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.environ.get('RETRY_DELAY', '1.0'))

def _get_context(user_id: str = None):
    """Enhanced context with session management."""
    base_context = {
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": FLASK_ENV,
        "platform": os.name,
        "system_status": "ready",
        "deployment": "render"
    }
    
    if user_id and user_id in user_sessions:
        session_data = user_sessions[user_id]
        base_context.update({
            "user_session": user_id,
            "session_start": session_data.get("session_start"),
            "query_count": session_data.get("query_count", 0),
            "last_query": session_data.get("last_query"),
            "preferences": session_data.get("preferences", {})
        })
    else:
        base_context["user_session"] = "demo-user-123"
    
    return base_context

def _update_session(user_id: str, query: str, result: dict):
    """Update user session data."""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "session_start": datetime.datetime.now().isoformat(),
            "query_count": 0,
            "last_query": None,
            "preferences": {}
        }
    
    user_sessions[user_id]["query_count"] += 1
    user_sessions[user_id]["last_query"] = query
    user_sessions[user_id]["last_result"] = result

def run_mcp_pipeline(query: str, user_id: str = None) -> dict:
    """Runs the MCP pipeline in a clean subprocess with session context."""
    try:
        # Enhanced context with session data
        context = _get_context(user_id)
        
        result = subprocess.run(
            [sys.executable, MCP_WORKER, query],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.join(os.path.dirname(os.path.abspath(__name__)), "mcp_project")
        )
        
        if result.returncode != 0:
            print(f"[Bridge] Worker stderr: {result.stderr}")
            error_response = {
                "context": context,
                "tools": [],
                "selected_tool": "error",
                "parameters": {},
                "result": {"error": result.stderr.strip() or "Worker process failed"}
            }
            _update_session(user_id, query, error_response)
            return error_response
        
        response = json.loads(result.stdout)
        response["context"] = context  # Override with enhanced context
        
        # Update session
        _update_session(user_id, query, response)
        
        return response
        
    except subprocess.TimeoutExpired:
        error_response = {
            "context": _get_context(user_id),
            "tools": [],
            "selected_tool": "error",
            "parameters": {},
            "result": {"error": "MCP pipeline timed out"}
        }
        _update_session(user_id, query, error_response)
        return error_response
    except json.JSONDecodeError as e:
        error_response = {
            "context": _get_context(user_id),
            "tools": [],
            "selected_tool": "error",
            "parameters": {},
            "result": {"error": f"Invalid JSON from worker: {e}"}
        }
        _update_session(user_id, query, error_response)
        return error_response

def run_mcp_pipeline_with_retry(query: str, user_id: str = None, max_retries: int = MAX_RETRIES) -> dict:
    """Runs the MCP pipeline with retry mechanism."""
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"[Retry] Attempt {attempt + 1}/{max_retries + 1} for query: '{query}'")
                time.sleep(RETRY_DELAY * attempt)  # Exponential backoff
            
            return run_mcp_pipeline(query, user_id)
            
        except subprocess.TimeoutExpired as e:
            last_error = f"Timeout on attempt {attempt + 1}: {str(e)}"
            print(f"[Retry] {last_error}")
            if attempt == max_retries:
                return {
                    "context": _get_context(user_id),
                    "tools": [],
                    "selected_tool": "error",
                    "parameters": {},
                    "result": {"error": f"Pipeline failed after {max_retries + 1} attempts: {str(e)}"},
                    "retry_info": {
                        "attempts": attempt + 1,
                        "max_retries": max_retries + 1,
                        "final_error": str(e)
                    }
                }
                
        except Exception as e:
            last_error = f"Error on attempt {attempt + 1}: {str(e)}"
            print(f"[Retry] {last_error}")
            if attempt == max_retries:
                return {
                    "context": _get_context(user_id),
                    "tools": [],
                    "selected_tool": "error",
                    "parameters": {},
                    "result": {"error": f"Pipeline failed after {max_retries + 1} attempts: {str(e)}"},
                    "retry_info": {
                        "attempts": attempt + 1,
                        "max_retries": max_retries + 1,
                        "final_error": str(e)
                    }
                }
    
    # Fallback (shouldn't reach here)
    return {
        "context": _get_context(user_id),
        "tools": [],
        "selected_tool": "error",
        "parameters": {},
        "result": {"error": "Unexpected error in retry mechanism"},
        "retry_info": {
            "attempts": max_retries + 1,
            "max_retries": max_retries + 1,
            "final_error": last_error
        }
    }

class QueryRequest:
    def __init__(self, data):
        self.query = data.get('query', '')
        self.user_id = data.get('user_id', session.get('user_id', 'demo-user-123'))

@app.route('/ask', methods=['POST'])
def ask():
    """Enhanced bridge endpoint with session management and retry mechanism."""
    data = request.get_json()
    query_request = QueryRequest(data)
    
    # Store user ID in session
    if 'user_id' in data:
        session['user_id'] = data['user_id']
    
    # Check if retry is requested
    use_retry = data.get('retry', False)
    max_retries = data.get('max_retries', MAX_RETRIES)
    
    print(f"\n{'='*50}")
    print(f"[API] Request received: '{query_request.query}' (User: {query_request.user_id}, Retry: {use_retry})")
    print(f"{'='*50}")
    
    try:
        if use_retry:
            response_data = run_mcp_pipeline_with_retry(query_request.query, query_request.user_id, max_retries)
        else:
            response_data = run_mcp_pipeline(query_request.query, query_request.user_id)
        
        print(f"[API] Returning response to frontend")
        print(f"[API] Selected tool: {response_data.get('selected_tool')}")
        print(f"[API] Result: {response_data.get('result')}")
        
        return jsonify(response_data)
        
    except Exception as e:
        traceback.print_exc()
        print(f"[API] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/batch', methods=['POST'])
def batch_ask():
    """Batch endpoint for executing multiple queries in sequence."""
    data = request.get_json()
    queries = data.get('queries', [])
    user_id = data.get('user_id', session.get('user_id', 'demo-user-123'))
    
    if not queries or not isinstance(queries, list):
        return jsonify({"error": "Invalid queries format. Expected array of query objects."}), 400
    
    # Store user ID in session
    if 'user_id' in data:
        session['user_id'] = data['user_id']
    
    print(f"\n{'='*50}")
    print(f"[API] Batch request received: {len(queries)} queries (User: {user_id})")
    print(f"{'='*50}")
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for i, query_item in enumerate(queries):
        query_text = query_item.get('query', '')
        query_id = query_item.get('id', f'query_{i+1}')
        
        try:
            print(f"[Batch] Processing query {i+1}: '{query_text}'")
            response_data = run_mcp_pipeline(query_text, user_id)
            
            # Add batch metadata
            response_data['batch_id'] = query_id
            response_data['batch_index'] = i
            response_data['success'] = True
            
            results.append(response_data)
            successful_count += 1
            
        except Exception as e:
            print(f"[Batch] Error in query {i+1}: {e}")
            error_response = {
                "batch_id": query_id,
                "batch_index": i,
                "query": query_text,
                "success": False,
                "error": str(e),
                "context": _get_context(user_id),
                "tools": [],
                "selected_tool": "error",
                "parameters": {},
                "result": {"error": str(e)}
            }
            results.append(error_response)
            failed_count += 1
    
    print(f"[Batch] Completed: {successful_count} successful, {failed_count} failed")
    
    return jsonify({
        "batch_summary": {
            "total_queries": len(queries),
            "successful": successful_count,
            "failed": failed_count,
            "user_id": user_id,
            "timestamp": datetime.datetime.now().isoformat()
        },
        "results": results
    })

@app.route('/session', methods=['GET'])
def get_session():
    """Get current session information."""
    user_id = session.get('user_id', 'demo-user-123')
    session_data = user_sessions.get(user_id, {
        "session_start": datetime.datetime.now().isoformat(),
        "query_count": 0,
        "preferences": {}
    })
    return jsonify({
        "user_id": user_id,
        "session_data": session_data,
        "context": _get_context(user_id)
    })

@app.route('/session', methods=['DELETE'])
def clear_session():
    """Clear current session."""
    user_id = session.get('user_id', 'demo-user-123')
    if user_id in user_sessions:
        del user_sessions[user_id]
    session.clear()
    return jsonify({"message": "Session cleared successfully"})

@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions (admin endpoint)."""
    return jsonify({
        "active_sessions": len(user_sessions),
        "sessions": user_sessions
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with system status."""
    try:
        # Test MCP pipeline with a simple query
        test_result = run_mcp_pipeline("test", "health-check")
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "mcp_status": "connected" if test_result.get('selected_tool') != 'error' else "error",
            "active_sessions": len(user_sessions),
            "environment": FLASK_ENV,
            "deployment": "render",
            "system_info": {
                "platform": os.name,
                "python_version": sys.version,
                "max_retries": MAX_RETRIES,
                "retry_delay": RETRY_DELAY
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "mcp_status": "error"
        }), 500

@app.route('/')
def root():
    return jsonify({
        "message": "Enhanced MCP Academic Demo API is running on Render",
        "version": "2.0",
        "environment": FLASK_ENV,
        "deployment": "render",
        "features": [
            "7 Academic Tools (GPA, Exams, Registration, etc.)",
            "Session Management & Persistence",
            "Batch Operations & Multiple Tool Execution",
            "Error Handling & Retry Mechanisms",
            "Enhanced UI Components",
            "Health Check Endpoint",
            "Query History Tracking"
        ],
        "endpoints": {
            "POST /ask": "Execute MCP query (with retry support)",
            "POST /batch": "Execute multiple queries in batch",
            "GET /session": "Get session info",
            "DELETE /session": "Clear session",
            "GET /sessions": "List all sessions (admin)",
            "GET /health": "System health check"
        },
        "tools_available": [
            "calculate_gpa", "check_exam_schedule", "register_course",
            "predict_grade", "track_assignment", "get_student_info", "calculate_credits_needed"
        ],
        "statistics": {
            "total_tools": 7,
            "max_retries": MAX_RETRIES,
            "retry_delay": f"{RETRY_DELAY}s"
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
