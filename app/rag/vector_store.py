import faiss
import numpy as np
from .embeddings import get_embedding

class VectorStore:
    def __init__(self, dim=384):
        self.index = faiss.IndexFlatL2(dim)
        self.documents = []

    def add_documents(self, docs):
        embeddings = [get_embedding(doc) for doc in docs]
        embeddings = np.array(embeddings).astype("float32")
        self.index.add(embeddings)
        self.documents.extend(docs)

    def search(self, query, k=3):
        query_vector = np.array([get_embedding(query)]).astype("float32")
        distances, indices = self.index.search(query_vector, k)
        return [self.documents[i] for i in indices[0]]