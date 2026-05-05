# Project Context: MCP Capstone Project

## Overview
This project is a Model Context Protocol (MCP) demonstration system that integrates a React frontend with an MCP server architecture. It showcases the communication flow from a user interface through a Flask/FastAPI bridge, down to an MCP client and server, and finally to actual tool execution.

## Architecture Pipeline
The architecture follows a distinct pipeline separating the frontend from the core MCP logic:
**React Frontend** → **API Bridge (Flask/FastAPI)** → **MCP Client** → **MCP Server** → **Tools**

### Architectural Layers
1. **Model Layer**: Handles tool selection logic based on the user's natural language queries.
2. **Context Layer**: Manages the system context, such as user session data, environment details, platform information, and timestamps.
3. **Tool Layer**: Manages the discovery of available tools and their execution through the MCP protocol.
4. **Execution Layer**: Contains the actual physical implementation of the tools (e.g., GPA calculation logic, exam scheduling logic).

## Directory Structure
The repository is split into the following primary components:

```
capstone-lab mid/
├── frontend/                    # Frontend application (React + Tailwind CSS)
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Main application pages (e.g., Dashboard)
│   │   └── services/            # API service integration
│   ├── package.json             # Node dependencies and scripts
│   ├── tailwind.config.js       # Tailwind styling configuration
│   └── vite.config.ts           # Vite build configuration
├── mcp_project/                 # Core MCP Implementation
│   ├── mcp_server/              # Server-side components for MCP
│   ├── client/                  # Client-side components for MCP interaction
│   ├── model/                   # Model logic for tool selection
│   ├── execution/               # Implementation details for specific tools
│   ├── server.py                # Main MCP server entry point
│   ├── _mcp_worker.py           # Worker script for the MCP pipeline
│   ├── client_bridge.py         # Bridge script connecting the client logic
│   └── run_demo.py              # Script for running a terminal demo
├── api.py                       # Initial API bridge attempt (FastAPI based)
├── api_flask.py                 # Final/Working API bridge (Flask based)
├── MCP_Capstone_Report.tex      # LaTeX report for the capstone project
└── README.md                    # Detailed instructions and documentation
```

## Available Tools (Execution Layer)
The MCP server currently exposes the following academic-focused tools:
1. **GPA Calculator (`calculate_gpa`)**
   - **Purpose**: Calculates GPA from a list of letter grades.
   - **Example Input**: `{"grades": ["A", "B", "A"]}`
   - **Example Output**: `{"text": "Calculated GPA: 3.67"}`
2. **Exam Schedule Checker (`check_exam_schedule`)**
   - **Purpose**: Returns the scheduled exam time for a specific course code.
   - **Example Input**: `{"course_code": "AI407"}`
   - **Example Output**: `{"text": "Exam for AI407: Monday 2:00 PM"}`

## Communication Protocol
The system enforces the strict use of the MCP Protocol for all tool execution. The standard JSON response format looks like this:
```json
{
  "context": {
    "timestamp": "...",
    "user_session": "demo-user-123",
    "environment": "academic-demonstration",
    "platform": "windows",
    "system_status": "ready"
  },
  "tools": ["calculate_gpa", "check_exam_schedule"],
  "selected_tool": "calculate_gpa",
  "parameters": {"grades": ["A", "B", "A"]},
  "result": {"text": "Calculated GPA: 3.67"}
}
```

## Technology Stack
- **Frontend**: React 18, TypeScript, TailwindCSS, Vite
- **UI Libraries**: Framer Motion, Radix UI, Lucide Icons
- **Backend / Bridge API**: Flask, Flask-CORS, Python 3.11+
- **Protocol**: MCP Python SDK (`mcp` library)

## How to Run the Project
1. **Start the MCP Server**: `cd mcp_project` -> `python server.py`
2. **Start the Backend API Bridge**: Navigate to root -> `python api_flask.py`
3. **Start the Frontend**: `cd frontend` -> `npm install` -> `npm run dev`

The frontend is typically available on `http://localhost:5173`, making POST requests to the Flask bridge at `http://localhost:8000/ask`.
