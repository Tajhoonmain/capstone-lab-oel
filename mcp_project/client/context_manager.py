import datetime


class ContextManager:
    """Manages system context for the MCP request."""

    def get_context(self) -> dict:
        """Loads and returns relevant system and session context."""
        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_session": "demo-user-123",
            "environment": "academic-demonstration",
            "platform": "windows-ps",
            "system_status": "ready",
        }
        print("Context loaded")
        return context
