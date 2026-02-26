import json
import re
import logging
import time

logger = logging.getLogger("agent_core")


class AgentCore:

    def __init__(self, llm, rag_registry, intent_classifier, tool_engine):
        self.llm = llm
        self.rag_registry = rag_registry
        self.intent_classifier = intent_classifier
        self.tool_engine = tool_engine

    # ---------------------------------------------------
    # PROMPT BUILDER
    # ---------------------------------------------------

    def _build_prompt(self, history, user_message, extra_context=""):

        formatted_history = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in history]
        )

        system_instruction = """
Eres un asistente empresarial.

Si necesitas ejecutar una herramienta,
responde ÚNICAMENTE en formato JSON con esta estructura:

{
  "type": "tool_call",
  "tool": "nombre_tool",
  "arguments": {
    "param": "valor"
  }
}

No agregues texto adicional fuera del JSON cuando invoques una tool.
"""

        user_prompt = f"""
Historial:
{formatted_history}

Contexto:
{extra_context}

USER: {user_message}
"""

        return system_instruction, user_prompt

    # ---------------------------------------------------
    # TOOL PARSER + EXECUTOR PROFESIONAL
    # ---------------------------------------------------

    def _try_execute_tool(self, response_text, tenant_id, session_id):

        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if not json_match:
                return None

            parsed = json.loads(json_match.group())

            if parsed.get("type") != "tool_call":
                return None

            tool_name = parsed.get("tool")
            arguments = parsed.get("arguments", {})

            logger.info(f"Executing tool: {tool_name} with args: {arguments}")

            start_time = time.time()

            try:
                result = self.tool_engine.execute(tool_name, arguments)

                execution_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "type": "tool_result",
                    "success": True,
                    "execution_time_ms": execution_time_ms,
                    "tool": tool_name,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "data": {
                        "arguments": arguments,
                        "result": result
                    }
                }

            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)

                logger.error(f"Tool execution failed: {str(e)}")

                return {
                    "type": "tool_result",
                    "success": False,
                    "execution_time_ms": execution_time_ms,
                    "tool": tool_name,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "error": str(e)
                }

        except Exception as e:
            logger.warning(f"Tool parsing failed: {str(e)}")

        return None

    # ---------------------------------------------------
    # MAIN ENTRYPOINT
    # ---------------------------------------------------

    def handle_message(
        self,
        tenant_id: str,
        session_id: str,
        user_message: str,
        session_manager
    ):

        # 1️⃣ Obtener historial
        history = session_manager.get_history(tenant_id, session_id)

        # 2️⃣ Guardar mensaje usuario
        session_manager.add_message(
            tenant_id, session_id, "user", user_message
        )

        # 3️⃣ Clasificar intención
        intent = self.intent_classifier.classify(user_message)

        extra_context = ""
        rag_used = False

        # 4️⃣ Routing por intención
        if intent == "RAG_QUERY":
            rag_pipeline = self.rag_registry.get_pipeline(tenant_id)
            extra_context = rag_pipeline.get_context(user_message)
            rag_used = True

        # 5️⃣ Construcción prompt
        system_prompt, user_prompt = self._build_prompt(
            history,
            user_message,
            extra_context
        )

        # 6️⃣ Llamar modelo
        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 7️⃣ Intentar ejecutar tool
        tool_result = self._try_execute_tool(
            response,
            tenant_id,
            session_id
        )

        if tool_result:
            final_response = tool_result
            assistant_message_for_memory = json.dumps(tool_result)
        else:
            final_response = {
                "type": "chat_response",
                "tenant_id": tenant_id,
                "session_id": session_id,
                "rag_used": rag_used,
                "response": response
            }
            assistant_message_for_memory = response

        # 8️⃣ Guardar respuesta en memoria
        session_manager.add_message(
            tenant_id, session_id, "assistant", assistant_message_for_memory
        )

        return final_response