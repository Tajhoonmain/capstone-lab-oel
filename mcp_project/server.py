import asyncio
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Task 1: Create a standalone MCP server
server = Server("University-Assistant")

@server.list_tools()
async def handle_list_tools():
    """Define structured tools with input schemas."""
    return [
        types.Tool(
            name="calculate_gpa",
            description="Calculate GPA from letter grades.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grades": {"type": "array", "items": {"type": "string", "enum": ["A", "B", "C", "D", "F"]}}
                },
                "required": ["grades"]
            }
        ),
        types.Tool(
            name="check_exam_schedule",
            description="Get exam schedule for a course.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_code": {"type": "string"}
                },
                "required": ["course_code"]
            }
        ),
        types.Tool(
            name="register_course",
            description="Register for a new course.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_code": {"type": "string"},
                    "course_name": {"type": "string"},
                    "credits": {"type": "integer"},
                    "semester": {"type": "string"}
                },
                "required": ["course_code", "course_name", "credits", "semester"]
            }
        ),
        types.Tool(
            name="predict_grade",
            description="Predict final grade based on current performance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_code": {"type": "string"},
                    "current_grade": {"type": "number"},
                    "assignments_remaining": {"type": "integer"},
                    "exam_weight": {"type": "number"}
                },
                "required": ["course_code", "current_grade", "assignments_remaining", "exam_weight"]
            }
        ),
        types.Tool(
            name="track_assignment",
            description="Track assignment status and deadlines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_name": {"type": "string"},
                    "course_code": {"type": "string"},
                    "due_date": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "submitted"]}
                },
                "required": ["assignment_name", "course_code", "due_date", "status"]
            }
        ),
        types.Tool(
            name="get_student_info",
            description="Get student academic information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"}
                },
                "required": ["student_id"]
            }
        ),
        types.Tool(
            name="calculate_credits_needed",
            description="Calculate credits needed for graduation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_credits": {"type": "integer"},
                    "major": {"type": "string"},
                    "target_year": {"type": "string"}
                },
                "required": ["current_credits", "major", "target_year"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
    """Execute tools via the MCP protocol."""
    if name == "calculate_gpa":
        grades = arguments.get("grades", [])
        pts = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        gpa = sum(pts.get(g.upper(), 0) for g in grades) / len(grades) if grades else 0.0
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Calculated GPA: {round(gpa, 2)}")],
            isError=False
        )
    elif name == "check_exam_schedule":
        course = arguments.get("course_code", "").upper()
        schedules = {
            "DS364": "Saturday 10:00 AM - 11:00 AM - Seminar Hall (Full stack)",
            "CS464": "Saturday 2:30 PM - 3:30 PM - Brabers (DNS)",
            "HM425": "Sunday 8:00 AM - 9:00 AM - Brabers (Cyber law)",
            "CS444": "Monday 2:30 PM - 3:30 PM - Quiz Hall FME (IR)",
            "MM101": "Monday 2:30 PM - 3:30 PM - Brabers (MM)",
            "CE408": "Tuesday 12:30 PM - 1:30 PM - Brabers (Cloud)"
        }
        time = schedules.get(course, f"No exam schedule found for {course}")
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Exam for {course}: {time}")],
            isError=False
        )
    elif name == "register_course":
        course_code = arguments.get("course_code", "")
        course_name = arguments.get("course_name", "")
        credits = arguments.get("credits", 0)
        semester = arguments.get("semester", "")
        
        # Simulate course registration
        registration_id = f"REG{hash(course_code + semester) % 10000}"
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Successfully registered for {course_code} ({course_name}) - {credits} credits - {semester}. Registration ID: {registration_id}")],
            isError=False
        )
    elif name == "predict_grade":
        course_code = arguments.get("course_code", "")
        current_grade = arguments.get("current_grade", 0)
        assignments_remaining = arguments.get("assignments_remaining", 0)
        exam_weight = arguments.get("exam_weight", 0.4)
        
        # Course mapping 
        courses = {
            "DS364": "Full Stack",
            "CS464": "DNS",
            "HM425": "Cyber Law",
            "CS444": "IR",
            "MM101": "MM",
            "CE408": "Cloud"
        }
        
        course_name = courses.get(course_code, "Course")
        
        # Simple grade prediction logic
        assignment_weight = 1 - exam_weight
        current_assignment_grade = current_grade / assignment_weight if assignment_weight > 0 else current_grade
        predicted_final = (current_assignment_grade * assignment_weight) + (85 * exam_weight)  # Assume 85 on final exam
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Grade prediction for {course_code} ({course_name}): Current {current_grade} → Predicted Final: {round(predicted_final, 2)} (assuming 85 on final exam)")],
            isError=False
        )
    elif name == "track_assignment":
        assignment_name = arguments.get("assignment_name", "")
        course_code = arguments.get("course_code", "")
        due_date = arguments.get("due_date", "")
        status = arguments.get("status", "pending")
        
        # Course mapping 
        courses = {
            "DS364": "Full Stack",
            "CS464": "DNS",
            "HM425": "Cyber Law",
            "CS444": "IR",
            "MM101": "MM",
            "CE408": "Cloud"
        }
        
        course_name = courses.get(course_code, "Course")
        
        # Simulate assignment tracking
        tracking_id = f"TRK{hash(assignment_name + course_code) % 10000}"
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Assignment tracked: '{assignment_name}' for {course_code} ({course_name}). Due: {due_date}. Status: {status}. Tracking ID: {tracking_id}")],
            isError=False
        )
    elif name == "get_student_info":
        student_id = arguments.get("student_id", "")
        
        # Simulate student database lookup
        students = {
            "2022907": {"name": "Maryam Taj", "major": "AI", "year": "Senior", "gpa": 3.7, "credits": 100},
            "2022106": {"name": "Arbaz", "major": "CS", "year": "Senior", "gpa": 3.2, "credits": 100},
            "2022002": {"name": "Aaiz", "major": "SE", "year": "Senior", "gpa": 3.9, "credits": 110}
        }
        
        info = students.get(student_id, {"name": "Unknown Student", "major": "Undeclared", "year": "Freshman", "gpa": 0.0, "credits": 0})
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Student Info: {info['name']} - {info['major']} ({info['year']}) - GPA: {info['gpa']}, Credits: {info['credits']}")],
            isError=False
        )
    elif name == "calculate_credits_needed":
        current_credits = arguments.get("current_credits", 0)
        major = arguments.get("major", "")
        target_year = arguments.get("target_year", "")
        
        # Credit requirements by major
        requirements = {
            "CS": 120,
            "AI": 115,
            "SE": 118,
        }
        
        required = requirements.get(major, 120)
        needed = max(0, required - current_credits)
        semesters_needed = (needed / 15) + (1 if needed % 15 > 0 else 0)  # Assume 15 credits per semester
        
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Credits needed for {major} graduation: {needed} more credits required (out of {required} total). Estimated {semesters_needed} semesters remaining to graduate by {target_year}.")],
            isError=False
        )
    else:
        raise ValueError(f"Tool not found: {name}")

async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="University-Assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
