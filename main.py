from dotenv import load_dotenv
load_dotenv()
import os
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Optional, Any, Dict, Union

from app.agent.agent_core import AgentCore
from app.rag.rag_registry import RAGRegistry
from app.memory.session_manager import SessionManager
from app.agent.intent_classifier import IntentClassifier
from app.tools.tool_engine import ToolEngine
from app.agent.llm_router import LLMRouter
from app.agent.mock_llm import MockLLM
from app.agent.hf_llm import HuggingFaceLLM

# ---------------------------------------------------
# Configuración de Logging
# ---------------------------------------------------

logger = logging.getLogger("api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

# ---------------------------------------------------
# Configuración de CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------

# Leer orígenes permitidos desde .env, con default para desarrollo local
allowed_origins_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
)

allowed_origins = [
    origin.strip() for origin in allowed_origins_env.split(",")
]

logger.info(f"CORS configurado para orígenes: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------
# Infraestructura (singletons simples)
# ---------------------------------------------------

rag_registry = RAGRegistry()
session_manager = SessionManager()
intent_classifier = IntentClassifier()
tool_engine = ToolEngine()

# ---------------------------------------------------
# Configuración dinámica de proveedores LLM
# ---------------------------------------------------

providers = {
    "mock": MockLLM()
}

if os.getenv("HF_API_TOKEN"):
    providers["hf"] = HuggingFaceLLM()

llm = LLMRouter(providers)

# ---------------------------------------------------
# Construcción del AgentCore
# ---------------------------------------------------

agent = AgentCore(
    llm=llm,
    rag_registry=rag_registry,
    intent_classifier=intent_classifier,
    tool_engine=tool_engine
)

# ---------------------------------------------------
# API Schemas
# ---------------------------------------------------

class ChatRequest(BaseModel):
    """
    Schema para solicitud de chat con validación integrada.
    
    - tenant_id: Identificador del tenant (1-100 caracteres, sin espacios en blanco)
    - session_id: Identificador de la sesión (1-100 caracteres, sin espacios en blanco)
    - message: Mensaje del usuario (1-2000 caracteres, sin espacios en blanco al inicio/fin)
    """
    tenant_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador único del tenant",
        example="empresa_demo"
    )
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador único de la sesión",
        example="session_001"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensaje del usuario",
        example="¿Cuál es el precio del vaso?"
    )
    
    class Config:
        """Configuración del modelo Pydantic"""
        str_strip_whitespace = True  # Elimina espacios al inicio/fin automáticamente


class ChatResponseData(BaseModel):
    """Respuesta de chat normal (sin tool execution)"""
    type: Literal["chat_response"] = Field(
        "chat_response",
        description="Tipo de respuesta"
    )
    tenant_id: str = Field(..., description="Identificador del tenant")
    session_id: str = Field(..., description="Identificador de la sesión")
    rag_used: bool = Field(..., description="Si se utilizó RAG para responder")
    response: str = Field(..., description="Texto de respuesta del agente")


class ToolResultDataSuccess(BaseModel):
    """Datos de ejecución exitosa de tool"""
    arguments: Dict[str, Any] = Field(..., description="Argumentos usados")
    result: Any = Field(..., description="Resultado de la herramienta")


class ToolResultDataError(BaseModel):
    """Datos de error en ejecución de tool"""
    error: str = Field(..., description="Mensaje de error")


class ToolResultResponse(BaseModel):
    """Respuesta de chat con ejecución de tool"""
    type: Literal["tool_result"] = Field(
        "tool_result",
        description="Tipo de respuesta"
    )
    tenant_id: str = Field(..., description="Identificador del tenant")
    session_id: str = Field(..., description="Identificador de la sesión")
    success: bool = Field(..., description="Si la ejecución fue exitosa")
    tool: str = Field(..., description="Nombre de la herramienta ejecutada")
    execution_time_ms: int = Field(..., description="Tiempo de ejecución en ms")
    data: Optional[Union[ToolResultDataSuccess, ToolResultDataError]] = Field(
        default=None,
        description="Datos de resultado o error"
    )


class UnifiedAgentResponse(BaseModel):
    """
    Respuesta unificada del agente.
    
    Puede ser de dos tipos:
    - chat_response: Respuesta de chat normal
    - tool_result: Resultado de ejecución de herramienta
    """
    response: Union[ChatResponseData, ToolResultResponse] = Field(
        ...,
        description="Respuesta del agente",
        discriminator="type"
    )


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Mensaje de error")
    error_type: str = Field(..., description="Tipo de error")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalles adicionales")

# ---------------------------------------------------
# Endpoints
# ---------------------------------------------------

@app.post("/chat", response_model=UnifiedAgentResponse)
def chat(request: ChatRequest):
    """
    Endpoint principal del chatbot comercial.
    
    Maneja:
    - Validación de inputs (via Pydantic)
    - Ejecución del agent
    - Captura de excepciones con logging
    
    **Request Body:**
    - tenant_id: Identificador del tenant (requerido, 1-100 caracteres)
    - session_id: Identificador de sesión (requerido, 1-100 caracteres)
    - message: Pregunta del usuario (requerido, 1-2000 caracteres)
    
    **Respuestas:**
    - 200: Procesamiento exitoso (ChatResponse o ToolResult)
    - 400: Validación fallida (campos vacíos, demasiado largos, etc.)
    - 500: Error interno del servidor
    """
    
    try:
        logger.info(
            f"Chat request recibido | tenant: {request.tenant_id} | "
            f"session: {request.session_id} | message_length: {len(request.message)}"
        )
        
        # Ejecutar agent con inputs ya validados
        agent_response = agent.handle_message(
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            user_message=request.message,
            session_manager=session_manager
        )
        
        logger.info(f"Chat completado exitosamente | tenant: {request.tenant_id}")
        
        # Envolver respuesta en schema unificado
        return UnifiedAgentResponse(response=agent_response)
    
    except HTTPException as e:
        # Re-lanzar excepciones HTTP de nivel aplicación
        raise
    
    except ValueError as e:
        logger.error(f"Error de validación de negocio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            f"Error interno al procesar chat | tenant: {request.tenant_id} | "
            f"session: {request.session_id} | error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el mensaje. Intenta nuevamente."
        )


@app.get("/")
def root():
    logger.info("Health check realizado")
    return {
        "status": "AI Commercial Agent running",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Enviar mensaje al agente",
            "GET /": "Health check"
        }
    }