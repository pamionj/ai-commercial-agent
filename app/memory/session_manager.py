class SessionManager:
    """
    Maneja memoria conversacional por tenant + sesión.
    Implementación actual: in-memory.
    Escalable a Redis/DB sin cambiar AgentCore.
    """

    def __init__(self):
        self._sessions = {}

    def _key(self, tenant_id: str, session_id: str):
        return f"{tenant_id}:{session_id}"

    def get_history(self, tenant_id: str, session_id: str):
        key = self._key(tenant_id, session_id)
        return self._sessions.get(key, [])

    def add_message(self, tenant_id: str, session_id: str, role: str, content: str):
        key = self._key(tenant_id, session_id)

        if key not in self._sessions:
            self._sessions[key] = []

        self._sessions[key].append({
            "role": role,
            "content": content
        })