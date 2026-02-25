class IntentClassifier:

    def classify(self, text: str) -> str:
        text = text.lower()

        if any(keyword in text for keyword in ["precio", "valor", "costo", "descuento"]):
            return "pricing"

        if any(keyword in text for keyword in ["envío", "despacho", "entrega"]):
            return "shipping"

        if any(keyword in text for keyword in ["horario", "atienden", "abierto"]):
            return "hours"

        if any(keyword in text for keyword in ["hola", "buenas", "gracias"]):
            return "smalltalk"

        return "general"