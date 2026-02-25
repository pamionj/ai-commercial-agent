from dotenv import load_dotenv
load_dotenv()
import logging
from fastapi import FastAPI
from app.agent.agent_core import AgentCore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

# Inicializar agente
agent = AgentCore()


@app.get("/")
def root():
    return {"status": "Commercial AI Agent ready"}


@app.get("/chat")
def chat(message: str):
    response = agent.handle_message(message)
    return {"response": response}
