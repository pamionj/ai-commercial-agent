import logging
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("session_manager")


class SessionStore(ABC):
    """
    Interfaz base para backends de almacenamiento de sesiones.
    
    Permite implementar diferentes estrategias:
    - In-memory (desarrollo)
    - Archivo JSON (desarrollo local con persistencia)
    - Redis (producción)
    - Base de datos (producción escalable)
    """

    @abstractmethod
    def get_history(self, tenant_id: str, session_id: str) -> List[Dict[str, str]]:
        """Obtiene o historial de una sesión"""
        pass

    @abstractmethod
    def add_message(self, tenant_id: str, session_id: str, role: str, content: str):
        """Agrega un mensaje a la sesión"""
        pass

    @abstractmethod
    def clear_session(self, tenant_id: str, session_id: str):
        """Limpia una sesión (opcional)"""
        pass


class InMemorySessionStore(SessionStore):
    """
    Almacenamiento de sesiones en memoria.
    
    Uso: Desarrollo local, testing
    Limitaciones: Se pierden datos al reiniciar
    """

    def __init__(self):
        self._sessions = {}
        logger.info("InMemorySessionStore inicializado")

    def _key(self, tenant_id: str, session_id: str) -> str:
        return f"{tenant_id}:{session_id}"

    def get_history(self, tenant_id: str, session_id: str) -> List[Dict[str, str]]:
        key = self._key(tenant_id, session_id)
        return self._sessions.get(key, [])

    def add_message(self, tenant_id: str, session_id: str, role: str, content: str):
        key = self._key(tenant_id, session_id)

        if key not in self._sessions:
            self._sessions[key] = []

        self._sessions[key].append({
            "role": role,
            "content": content
        })

    def clear_session(self, tenant_id: str, session_id: str):
        key = self._key(tenant_id, session_id)
        if key in self._sessions:
            del self._sessions[key]
            logger.info(f"Session cleared: {key}")


class FileSystemSessionStore(SessionStore):
    """
    Almacenamiento de sesiones en archivos JSON.
    
    Uso: Desarrollo local con persistencia
    Estructura: data/sessions/{tenant_id}/{session_id}.json
    Ventajas: Persistencia, fácil de inspeccionar, debugging
    Limitaciones: No es escalable (problemas con concurrencia)
    """

    def __init__(self, base_path: str = "data/sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileSystemSessionStore inicializado en: {self.base_path}")

    def _get_session_path(self, tenant_id: str, session_id: str) -> Path:
        """Construye la ruta del archivo de sesión"""
        tenant_path = self.base_path / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        return tenant_path / f"{session_id}.json"

    def get_history(self, tenant_id: str, session_id: str) -> List[Dict[str, str]]:
        """Lee historial desde archivo"""
        path = self._get_session_path(tenant_id, session_id)

        if not path.exists():
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", [])
        except Exception as e:
            logger.error(f"Error reading session file {path}: {e}")
            return []

    def add_message(self, tenant_id: str, session_id: str, role: str, content: str):
        """Agrega mensaje y persiste a archivo"""
        path = self._get_session_path(tenant_id, session_id)

        try:
            # Leer mensajes existentes
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
            else:
                messages = []

            # Agregar nuevo mensaje
            messages.append({
                "role": role,
                "content": content
            })

            # Guardar
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "messages": messages
                    },
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception as e:
            logger.error(f"Error writing session file {path}: {e}")
            raise

    def clear_session(self, tenant_id: str, session_id: str):
        """Elimina archivo de sesión"""
        path = self._get_session_path(tenant_id, session_id)

        try:
            if path.exists():
                path.unlink()
                logger.info(f"Session file deleted: {path}")
        except Exception as e:
            logger.error(f"Error deleting session file {path}: {e}")


class SessionManager:
    """
    Gestor de sesiones con soporte a múltiples backends.
    
    Permite usar distintos almacenamientos:
    - InMemorySessionStore: Rápido, para desarrollo
    - FileSystemSessionStore: Con persistencia local
    - (Futuro) RedisSessionStore: Para escala
    
    Configuración via variable de entorno:
    - SESSION_STORE: "memory" (default), "filesystem"
    """

    def __init__(self, store: SessionStore = None):
        """
        Inicializa SessionManager con un backend.
        
        Args:
            store: Instancia de SessionStore. Si es None, usa default según .env
        """
        if store is None:
            import os
            store_type = os.getenv("SESSION_STORE", "memory").lower()

            if store_type == "filesystem":
                store = FileSystemSessionStore()
            else:
                store = InMemorySessionStore()

        self.store = store
        logger.info(f"SessionManager inicializado con: {type(store).__name__}")

    def get_history(self, tenant_id: str, session_id: str) -> List[Dict[str, str]]:
        """Obtiene historial de mensajes"""
        return self.store.get_history(tenant_id, session_id)

    def add_message(self, tenant_id: str, session_id: str, role: str, content: str):
        """Agrega mensaje a la sesión"""
        self.store.add_message(tenant_id, session_id, role, content)

    def clear_session(self, tenant_id: str, session_id: str):
        """Limpia una sesión"""
        self.store.clear_session(tenant_id, session_id)