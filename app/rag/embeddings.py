from sentence_transformers import SentenceTransformer

# Modelo liviano y eficiente (384 dimensiones)
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    return model.encode(text)