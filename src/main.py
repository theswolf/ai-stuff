import logging
import os
import time
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from .agent_router import router as agent_router
from .llm_client import get_llm_client
from .logging_config import setup_logging, RequestLoggingMiddleware
from .rag_router import router as rag_router

load_dotenv()
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Engineer Service", description="Chat + RAG + Agent service", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)
app.include_router(rag_router)
app.include_router(agent_router)
Instrumentator().instrument(app).expose(app)


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1, max_length=50)
    system_prompt: str | None = Field(default=None, max_length=5000)
    stream: bool = False


class ChatResponse(BaseModel):
    id: str
    content: str
    model: str
    latency_ms: float


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-engineer-service"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Chat request: {len(request.messages)} messages")
    start_time = time.time()
    try:
        client = get_llm_client()
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        if request.stream:
            def generate():
                for chunk in client.chat_stream(messages, request.system_prompt):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(generate(), media_type="text/event-stream")
        content = client.chat(messages, request.system_prompt)
        latency_ms = (time.time() - start_time) * 1000
        return ChatResponse(id=request_id, content=content, model=str(type(client).__name__), latency_ms=latency_ms)
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@app.post("/chat/simple")
async def simple_chat(message: str, system: str = "Sei un assistente utile."):
    client = get_llm_client()
    response = client.chat(messages=[{"role": "user", "content": message}], system_prompt=system)
    return {"response": response}
