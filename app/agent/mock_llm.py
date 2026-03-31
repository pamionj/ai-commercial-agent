from .llm_interface import LLMInterface
import re


class MockLLM(LLMInterface):

    def generate(self, system_prompt: str, user_prompt: str) -> str:

        # -----------------------------------------
        # Extraer pregunta del cliente
        # -----------------------------------------
        try:
            if "Pregunta del cliente:" in user_prompt:
                last_user_message = user_prompt.split("Pregunta del cliente:")[-1].strip()
            elif "USER:" in user_prompt:
                last_user_message = user_prompt.split("USER:")[-1].strip()
            else:
                last_user_message = user_prompt
        except Exception:
            last_user_message = user_prompt

        text = last_user_message.lower()

        print("DEBUG last_user_message:", repr(last_user_message))
        print("DEBUG text:", repr(text))

        # -----------------------------------------
        # 1️⃣ Small talk
        # -----------------------------------------
        if any(word in text for word in ["hola", "buenas"]):
            return "¡Hola! 👋 ¿En qué puedo ayudarte hoy?"

        if "gracias" in text:
            return "Con gusto. Si necesitas algo más, estoy aquí para ayudarte."

        # -----------------------------------------
        # 2️⃣ Tool simulation
        # -----------------------------------------
        if "estudiante" in text:

            match = re.search(r"\d+", text)
            student_id = match.group(0) if match else ""

            return f"""
{{
  "type": "tool_call",
  "tool": "get_student_status",
  "arguments": {{
    "student_id": "{student_id}"
  }}
}}
"""

        # -----------------------------------------
        # 3️⃣ RAG simulation limpia
        # -----------------------------------------
        extra_context = ""

        try:
            if "Información relevante:" in user_prompt:
                extra_context = user_prompt.split("Información relevante:")[-1]
                if "Pregunta del cliente:" in extra_context:
                    extra_context = extra_context.split("Pregunta del cliente:")[0]
                extra_context = extra_context.strip()
        except Exception:
            extra_context = ""

        print("DEBUG extra_context:", repr(extra_context))

        if extra_context:
            return (
                f"{extra_context}\n\n"
                "¿Deseas que prepare una cotización?"
            )

        # -----------------------------------------
        # 4️⃣ Default
        # -----------------------------------------
        return "Entiendo tu consulta. ¿Podrías darme más detalles?"