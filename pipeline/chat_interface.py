"""
Chat interface module: Handles user input/output and entry point for the pipeline.
"""

class ChatInterface:
    def __init__(self):
        pass

    def get_user_query(self, query):
        """Receive user query from frontend (as argument)."""
        return query

    def send_response(self, response):
        """Send response to user (stub)."""
        pass
