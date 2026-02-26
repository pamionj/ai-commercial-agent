from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.agent_core import AgentCore
from app.rag.rag_registry import RAGRegistry
from app.memory.session_manager import SessionManager
from app.agent.intent_classifier import IntentClassifier
from app.tools.tool_engine import ToolEngine
from app.agent.llm_router import LLMRouter
from app.agent.mock_llm import MockLLM
from app.agent.hf_llm import HuggingFaceLLM

app = FastAPI()

# Infraestructura (singletons simples)
rag_registry = RAGRegistry()
session_manager = SessionManager()
intent_classifier = IntentClassifier()
tool_engine = ToolEngine()

llm = LLMRouter({
    "mock": MockLLM(),
    # "hf": HuggingFaceLLM(...)
})

agent = AgentCore(
    llm=llm,
    rag_registry=rag_registry,
    intent_classifier=intent_classifier,
    tool_engine=tool_engine
)


class ChatRequest(BaseModel):
    tenant_id: str
    session_id: str
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    response = agent.handle_message(
        tenant_id=request.tenant_id,
        session_id=request.session_id,
        user_message=request.message,
        session_manager=session_manager
    )
    return {"response": response}

@app.get("/")
def root():
    return {"status": "AI Commercial Agent running"}