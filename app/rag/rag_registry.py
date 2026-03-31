class RAGRegistry:
    """
    Mantiene instancias RAG en memoria por tenant.
    Evita reconstrucción innecesaria.
    """

    def __init__(self):
        self._pipelines = {}

    def get_pipeline(self, tenant_id: str):
        if tenant_id not in self._pipelines:
            from app.rag.rag_pipeline import RAGPipeline
            self._pipelines[tenant_id] = RAGPipeline(tenant_id)

        return self._pipelines[tenant_id]

    def reindex(self, tenant_id: str):
        pipeline = self.get_pipeline(tenant_id)
        pipeline.reindex()