from .llm_interface import LLMInterface


class MockLLM(LLMInterface):

    def generate(self, system_prompt: str, user_prompt: str) -> str:

        # Extraer solo la parte del contexto
        context = ""
        if "Contexto:" in user_prompt and "Pregunta:" in user_prompt:
            context = user_prompt.split("Contexto:")[1].split("Pregunta:")[0].strip()

        # Si no hay contexto
        if not context:
            return "No encontré información suficiente para responder tu consulta."

        # Construir respuesta más natural
        response = (
            "Gracias por tu consulta.\n\n"
            "Estos son los detalles relevantes:\n\n"
            f"{context}\n\n"
            "Si deseas una cotización personalizada o más información, puedo ayudarte."
        )

        return response