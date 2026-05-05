import logging
import os
from .llm_interface import LLMInterface
import re

logger = logging.getLogger("mock_llm")


class MockLLM(LLMInterface):
    """
    Mock LLM para testing y desarrollo local.
    
    Simula respuestas sin consumir API tokens.
    Útil para:
    - Testing de arquitectura
    - Desarrollo sin costos
    - Validación de flujos end-to-end
    
    Comportamiento:
    - Detecta intención por palabras clave
    - Simula tool calls cuando detecta "estudiante"
    - Simula RAG cuando hay contexto en prompt
    - Responde small talk naturalmente
    """

    def __init__(self):
        """Inicializa MockLLM con configuración de testing"""
        self.verbose = os.getenv("MOCK_LLM_VERBOSE", "false").lower() == "true"
        logger.info("MockLLM inicializado (verbose=%s)", self.verbose)

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

        text = last_user_message.lower().strip()

        logger.debug(f"Extracted user message: {repr(last_user_message)}")
        logger.debug(f"Lowercased text: {repr(text)}")

        if self.verbose:
            logger.info(f"MockLLM processing: {repr(last_user_message[:50])}")

        # -----------------------------------------
        # 1️⃣ Detectar saludo / Small talk
        # -----------------------------------------
        greeting_words = ["hola", "buenas", "buenos", "hi", "hey", "¿qué tal"]
        if any(word in text for word in greeting_words):
            logger.info("MockLLM: Detected greeting")
            return "¡Hola! 👋 Soy tu asistente comercial. ¿En qué puedo ayudarte?"

        gratitude_words = ["gracias", "thanks", "muchas gracias", "agradezco"]
        if any(word in text for word in gratitude_words):
            logger.info("MockLLM: Detected gratitude")
            return "Con gusto 😊. Si necesitas algo más, estoy aquí para ayudarte."

        # -----------------------------------------
        # 2️⃣ Simular Tool Call (Get Student Status)
        # -----------------------------------------
        tool_keywords = ["estudiante", "alumno", "matrícula", "student", "status"]
        if any(keyword in text for keyword in tool_keywords):
            logger.info("MockLLM: Detected tool intent - generating tool_call")

            # Extraer ID de estudiante si está disponible
            match = re.search(r"\d+", text)
            student_id = match.group(0) if match else "1024"

            tool_response = f"""
{{
  "type": "tool_call",
  "tool": "get_student_status",
  "arguments": {{
    "student_id": "{student_id}"
  }}
}}
"""
            if self.verbose:
                logger.info(f"Tool call response: {repr(tool_response)}")
            return tool_response

        # -----------------------------------------
        # 3️⃣ Detectar contenido RAG y responder
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

        if extra_context:
            logger.info("MockLLM: Detected RAG context - responding with context")
            logger.debug(f"Context: {repr(extra_context[:100])}")

            # Simular respuesta basada en contexto
            if "precio" in text or "costo" in text or "valor" in text:
                if "$" in extra_context:
                    # Extraer precio si está en la respuesta
                    price_match = re.search(r"\$(\d+)", extra_context)
                    if price_match:
                        price = price_match.group(0)
                        product_match = re.search(r"(\w+):\s*" + re.escape(price), extra_context)
                        if product_match:
                            product = product_match.group(1)
                            return f"El precio de {product.lower()} es {price} por unidad."
                        return f"El precio es {price} por unidad."

            if self.verbose:
                logger.info(f"Raw context response: {repr(extra_context[:100])}")

            return (
                f"{extra_context}\n\n"
                "¿Te gustaría que prepare una cotización o tienes más preguntas?"
            )

        # -----------------------------------------
        # 4️⃣ Keywords específicas de tema
        # -----------------------------------------
        rag_keywords = {
            "precio": "Para consultar precios, necesito buscar en nuestro catálogo. ¿Qué producto específico te interesa?",
            "envío": "Sobre entregas: trabajamos con múltiples opciones de despacho. ¿Cuál es tu ubicación?",
            "descuento": "Tenemos promociones especiales. ¿Cuál es tu volumen de compra?",
            "producto": "Contamos con una amplia variedad de productos. ¿Qué tipo buscas?",
            "vaso": "Tenemos vasos reutilizables de alta calidad. ¿Deseas conocer opciones?",
            "plato": "Disponemos de platos ecológicos. ¿Prefieres algún material específico?",
        }

        for keyword, response in rag_keywords.items():
            if keyword in text:
                logger.info(f"MockLLM: Detected RAG keyword '{keyword}'")
                return response

        # -----------------------------------------
        # 5️⃣ Default Response
        # -----------------------------------------
        logger.info("MockLLM: No specific intent detected - generic response")
        return (
            "Entiendo tu consulta. Para darte una respuesta más precisa, "
            "necesito más detalles. ¿Podrías especificar qué tipo de ayuda necesitas?"
        )