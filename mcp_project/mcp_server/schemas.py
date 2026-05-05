# Note: Schema definition for clarity in the project
# This can be used for documentation or validation within the server logic

EXAM_SCHEMA = {
    "name": "check_exam_schedule",
    "description": "Check exam timing for a course",
    "input_schema": {"type": "object", "properties": {"course_code": {"type": "string"}}, "required": ["course_code"]},
}

GPA_SCHEMA = {
    "name": "calculate_gpa",
    "description": "Calculate GPA from grades",
    "input_schema": {
        "type": "object",
        "properties": {"grades": {"type": "array", "items": {"type": "string", "enum": ["A", "B", "C", "D", "F"]}}},
        "required": ["grades"],
    },
}
