class ModelLayer:
    """Logic to decide which tool to call based on the user query."""

    def decide_tool(self, user_query: str, available_tools: list) -> tuple[str, dict]:
        """
        Analyzes the query and selects the best tool.
        Returns (tool_name, parameters).
        """
        query = user_query.lower()
        tool_names = [tool.name for tool in available_tools]

        selected_tool = "none"
        parameters = {}

        if "gpa" in query or "calculate" in query:
            selected_tool = "calculate_gpa"
            # Simple simulation: Extract grades or use default for demo
            parameters = {"grades": ["A", "B", "A"]}
        elif "exam" in query or "schedule" in query:
            selected_tool = "check_exam_schedule"
            parameters = {"course_code": "AI407"}

        print(f"Model selected tool: {selected_tool}")
        return selected_tool, parameters
