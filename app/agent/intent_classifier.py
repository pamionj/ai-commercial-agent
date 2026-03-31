class IntentClassifier:
    """
    Clasificador de intención orientado a arquitectura del agente.

    No clasifica por tema.
    Clasifica por tipo de procesamiento requerido:
    - TOOL_CALL
    - RAG_QUERY
    - GENERAL_CHAT
    """

    def classify(self, text: str) -> str:
        text = text.lower()

        # ---- TOOL INTENT ----
        # Consultas sobre estado de estudiante
        if any(keyword in text for keyword in ["estudiante", "alumno", "estado", "matrícula"]):
            return "STUDENT_STATUS"

        # ---- RAG INTENT ----
        # Preguntas sobre productos, precios, despacho, descuentos
        if any(keyword in text for keyword in [
            "precio", "valor", "costo", "descuento",
            "envío", "despacho", "entrega",
            "producto", "vasos", "plato", "cubiertos"
        ]):
            return "RAG_QUERY"

        # ---- SMALL TALK ----
        if any(keyword in text for keyword in ["hola", "buenas", "gracias"]):
            return "GENERAL_CHAT"

        # Default
        return "GENERAL_CHAT"