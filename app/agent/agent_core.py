import json
import re
import logging

from app.agent.hf_llm import HuggingFaceLLM
from app.agent.mock_llm import MockLLM
from app.agent.llm_router import LLMRouter
from app.tools.tool_executor import execute_tool


logger = logging.getLogger("agent_core")


class Memory:
    def __init__(self):
        self.history = []

    def add(self, role, content):
        self.history.append({"role": role, "content": content})

    def get_context(self):
        return "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in self.history]
        )


class AgentCore:
    def __init__(self):
        #  MULTI-PROVIDER CON FALLBACK
        self.llm = LLMRouter({
        "hf": HuggingFaceLLM(),  # Provider principal
        "mock": MockLLM()          # Fallback automático
        })

        self.memory = Memory()

    def build_prompt(self, user_message):
        context = self.memory.get_context()

        system_instruction = """
Eres un asistente académico.

Si el usuario pregunta por el estado de un estudiante,
debes responder ÚNICAMENTE en formato JSON usando esta estructura:

{
  "tool": "get_student_status",
  "arguments": {
    "student_id": "ID_AQUI"
  }
}

No agregues texto adicional.
No expliques nada.
Solo responde JSON válido.
"""

        user_prompt = f"""
Historial:
{context}

USER: {user_message}
"""

        return system_instruction, user_prompt

    def handle_message(self, user_message):
        # Guardar mensaje del usuario
        self.memory.add("user", user_message)

        # Construir prompts separados
        system_prompt, user_prompt = self.build_prompt(user_message)

        # Llamar al LLM (ahora pasa por el router)
        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # Guardar respuesta cruda
        self.memory.add("assistant_raw", response)

        # ---- DETECCIÓN ROBUSTA DE TOOL ----
        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)

            if json_match:
                parsed = json.loads(json_match.group())

                if "tool" in parsed:
                    tool_name = parsed["tool"]
                    arguments = parsed.get("arguments", {})

                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    tool_result = execute_tool(tool_name, arguments)

                    final_response = f"Resultado de herramienta: {tool_result}"

                    self.memory.add("assistant", final_response)
                    return final_response

        except Exception as e:
            logger.warning(f"Tool parsing failed: {str(e)}")
        # -----------------------------------

        # Si no es tool, devolver texto normal
        self.memory.add("assistant", response)
        return response