"""
MCP Worker — Runs the full MCP pipeline in an isolated process.

This script is called by client_bridge.py as a subprocess.
It receives a user query as argv[1], performs the full MCP pipeline,
and prints a JSON response to stdout.

All print() for logging goes to stderr so stdout stays clean for JSON.
"""

import asyncio
import json
import os
import sys
import datetime

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


def log(msg):
    """Log to stderr so stdout stays clean for JSON output."""
    print(msg, file=sys.stderr)


def get_context() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_session": "demo-user-123",
        "environment": "academic-demonstration",
        "platform": "windows",
        "system_status": "ready",
    }


import re


def decide_tool(query: str, tool_names: list) -> tuple:
    """Model Layer: Decide which tool to use and parse real-time parameters from the query."""
    q = query.lower()

    # Helper to extract course code (e.g., CS301, AI 407, DS-364)
    def get_course():
        match = re.search(r"[a-z]{2,4}\s*-?\s*\d{3,4}", q)
        return match.group(0).upper().replace(" ", "").replace("-", "") if match else "DS364"

    # Course naming mapping
    courses = {
        "DS364": "Full Stack",
        "CS464": "DNS",
        "HM425": "Cyber Law",
        "CS444": "IR",
        "MM101": "MM",
        "CE408": "Cloud",
    }

    # Course registration queries (most specific first)
    if any(word in q for word in ["register", "enroll", "add course", "sign up"]):
        course_code = get_course()
        return "register_course", {
            "course_code": course_code,
            "course_name": courses.get(course_code, "Selected Course"),
            "credits": 3,
            "semester": "Fall 2024",
        }

    # Student information queries
    elif any(word in q for word in ["student info", "profile", "my information", "who am i", "student id"]):
        st_match = re.search(r"\d{7}", q)
        student_id = st_match.group(0) if st_match else "2022907"
        return "get_student_info", {"student_id": student_id}

    # Grade prediction queries
    elif any(word in q for word in ["predict", "forecast", "what grade", "final grade"]):
        num_match = re.search(r"(\d+(\.\d+)?)", q)
        current_grade = float(num_match.group(1)) if num_match else 82.5
        return "predict_grade", {
            "course_code": get_course(),
            "current_grade": current_grade,
            "assignments_remaining": 2,
            "exam_weight": 0.4,
        }

    # Assignment tracking queries
    elif any(word in q for word in ["assignment", "homework", "track", "deadline"]):
        return "track_assignment", {
            "assignment_name": "User Specified Homework",
            "course_code": get_course(),
            "due_date": "2024-04-15",
            "status": "pending",
        }

    # Credit calculation queries
    elif any(word in q for word in ["credits", "graduate", "graduation", "how many"]):
        num_match = re.search(r"(\d+)", q)
        credits_count = int(num_match.group(1)) if num_match else 100

        # Simple major extraction
        major = "CS"
        if "se" in q or "software" in q:
            major = "SE"
        elif "ai" in q or "artificial" in q:
            major = "AI"

        return "calculate_credits_needed", {"current_credits": credits_count, "major": major, "target_year": "2025"}

    # Exam schedule queries
    elif "exam" in q or "schedule" in q or "when" in q:
        return "check_exam_schedule", {"course_code": get_course()}

    # GPA related queries (most general, last)
    elif "gpa" in q or "calculate" in q or "grade" in q:
        # Match single isolated letter grades
        grades = re.findall(r"\b[a-df]\b", q)
        if not grades:
            grades = ["a", "b", "a"]  # Fallback
        return "calculate_gpa", {"grades": [g.upper() for g in grades]}

    return "none", {}


async def run_pipeline(user_query: str) -> dict:
    context = get_context()
    log("Context loaded")

    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "server.py"))

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", server_path],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discovery
            list_result = await session.list_tools()
            tools = getattr(list_result, "tools", [])
            tool_names = [t.name for t in tools]
            log(f"Tools discovered: {tool_names}")

            # Model decision
            selected_tool, parameters = decide_tool(user_query, tool_names)
            log(f"Model selected tool: {selected_tool}")

            result = {"message": "No matching tool found for this query."}

            if selected_tool != "none" and selected_tool in tool_names:
                log(f"Executing tool '{selected_tool}' via MCP")
                call_result = await session.call_tool(selected_tool, arguments=parameters)

                if hasattr(call_result, "content") and call_result.content:
                    result = {"text": call_result.content[0].text}
                else:
                    result = {"raw": str(call_result)}

            log("Returning response to frontend")

            return {
                "context": context,
                "tools": tool_names,
                "selected_tool": selected_tool,
                "parameters": parameters,
                "result": result,
            }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)

    query = sys.argv[1]

    try:
        response = asyncio.run(run_pipeline(query))
        # Print ONLY the JSON to stdout
        print(json.dumps(response))
    except Exception as e:
        log(f"Pipeline error: {e}")
        context = get_context()
        print(
            json.dumps(
                {
                    "context": context,
                    "tools": [],
                    "selected_tool": "error",
                    "parameters": {},
                    "result": {"error": str(e)},
                }
            )
        )


if __name__ == "__main__":
    main()
