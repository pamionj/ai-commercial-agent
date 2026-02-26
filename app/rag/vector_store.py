import faiss
import numpy as np
import os


class VectorStore:
    """
    Vector store basado en FAISS con persistencia a disco.
    Diseñado para arquitectura multi-tenant.
    """

    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = index_path.replace(".faiss", "_meta.npy")

        if os.path.exists(self.index_path):
            self._load()
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.text_chunks = []

    def add(self, embeddings: np.ndarray, texts: list):
        self.index.add(embeddings)
        self.text_chunks.extend(texts)

    def search(self, query_embedding: np.ndarray, top_k=3):
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.text_chunks):
                results.append(self.text_chunks[idx])

        return results

    def save(self):
        """
        Guarda índice FAISS y metadata en disco.
        """
        faiss.write_index(self.index, self.index_path)
        np.save(self.metadata_path, np.array(self.text_chunks, dtype=object))

    def _load(self):
        """
        Carga índice FAISS y metadata desde disco.
        """
        self.index = faiss.read_index(self.index_path)
        self.text_chunks = np.load(self.metadata_path, allow_pickle=True).tolist()