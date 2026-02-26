class Retriever:

    def __init__(self, embedding_model, vector_store):
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k=3):
        query_embedding = self.embedding_model.encode(query)
        results = self.vector_store.search(query_embedding, top_k)
        return results