from app.tools.student_tools import get_student_status


def execute_tool(tool_name: str, arguments: dict):

    if tool_name == "get_student_status":
        return get_student_status(**arguments)

    return "Tool no reconocida"