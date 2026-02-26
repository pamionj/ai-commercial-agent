from pathlib import Path
import re

from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever


class RAGPipeline:
    """
    Pipeline RAG multi-tenant con persistencia FAISS.
    - Carga índice si existe
    - Si no existe, lo construye automáticamente
    - Permite reindex explícito
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.base_path = Path(f"data/tenants/{tenant_id}")
        self.knowledge_path = self.base_path / "knowledge.txt"
        self.index_path = self.base_path / "index.faiss"

        self.base_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model = EmbeddingModel()

        self.vector_store = None
        self.retriever = None

        self._initialize()

    # ---------------------------------------------------
    # Inicialización del índice
    # ---------------------------------------------------
    def _initialize(self):
        documents = DocumentLoader(str(self.knowledge_path)).load()

        if not documents:
            documents = [""]  # Evita error si archivo vacío

        embeddings = self.embedding_model.encode(documents)
        dimension = embeddings.shape[1]

        self.vector_store = VectorStore(dimension, str(self.index_path))

        # Si es nuevo índice, lo construye
        if not self.vector_store.text_chunks:
            self.vector_store.add(embeddings, documents)
            self.vector_store.save()

        self.retriever = Retriever(self.embedding_model, self.vector_store)

    # ---------------------------------------------------
    # Reindex manual
    # ---------------------------------------------------
    def reindex(self):
        documents = DocumentLoader(str(self.knowledge_path)).load()

        if not documents:
            documents = [""]

        embeddings = self.embedding_model.encode(documents)
        dimension = embeddings.shape[1]

        self.vector_store = VectorStore(dimension, str(self.index_path))
        self.vector_store.add(embeddings, documents)
        self.vector_store.save()

        self.retriever = Retriever(self.embedding_model, self.vector_store)

    # ---------------------------------------------------
    # Extracción estructurada de precio
    # ---------------------------------------------------
    def extract_price_from_docs(self, docs: list[str]) -> str | None:
        """
        Busca patrones tipo:
        Producto: $123 por unidad.
        """
        price_pattern = re.compile(r"\$(\d+)")

        for doc in docs:
            if "$" in doc:
                match = price_pattern.search(doc)
                if match:
                    price = match.group(0)
                    product_name = doc.split(":")[0]
                    return f"El precio de {product_name.lower()} es {price} por unidad."

        return None

    # ---------------------------------------------------
    # Recuperación de contexto
    # ---------------------------------------------------
    def get_context(self, query: str, top_k: int = 2):
        retrieved_docs = self.retriever.retrieve(query, top_k)

        if not retrieved_docs:
            return ""

        # Intentar respuesta estructurada primero
        structured_price = self.extract_price_from_docs(retrieved_docs)
        if structured_price:
            return structured_price

        # Si no aplica extracción estructurada, devolver contexto normal
        context = "\n\n".join(retrieved_docs)
        return f"\n\nContexto relevante:\n{context}\n"