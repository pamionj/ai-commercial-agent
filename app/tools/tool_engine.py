from app.tools.tool_executor import execute_tool


class ToolEngine:
    """
    Adaptador OO para sistema de tools existente.
    Permite futura extensión sin romper arquitectura.
    """

    def execute(self, tool_name: str, arguments: dict):
        return execute_tool(tool_name, arguments)