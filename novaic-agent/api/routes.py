"""
NovAIC Agent API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import os
import json
from datetime import datetime

from .schemas import (
    InitRequest, InitResponse,
    ChatRequest, ChatResponse, ChatResult,
    FileUploadResponse, FileListResponse,
    HistoryResponse, HealthResponse
)
from core.agent import NBCCAgent
from config import settings

router = APIRouter()

# Global agent instance
_agent: Optional[NBCCAgent] = None


def get_agent() -> NBCCAgent:
    """Get the global agent instance"""
    if _agent is None:
        raise HTTPException(
            status_code=400,
            detail="Agent not initialized. Call /api/init first."
        )
    return _agent


# ==================== Init ====================

@router.post("/init", response_model=InitResponse)
async def init_agent(request: InitRequest):
    """Initialize the Agent with multi-provider support"""
    global _agent
    
    provider = request.provider
    print(f"[Init] Received request: provider={provider}, model={request.model}")
    
    # Update common settings
    if request.model:
        settings.default_model = request.model
    if request.max_tokens is not None:
        settings.max_tokens = request.max_tokens
    if request.max_iterations is not None:
        settings.max_iterations = request.max_iterations
    if request.visible_shell is not None:
        settings.visible_shell = request.visible_shell
    
    # Update provider-specific settings
    if request.openai:
        if request.openai.api_key:
            settings.openai_api_key = request.openai.api_key
        settings.openai_override_base_url = request.openai.override_base_url
        if request.openai.api_base:
            settings.openai_api_base = request.openai.api_base
    
    if request.anthropic:
        if request.anthropic.api_key:
            settings.anthropic_api_key = request.anthropic.api_key
        if request.anthropic.api_base:
            settings.anthropic_api_base = request.anthropic.api_base
    
    if request.google:
        if request.google.api_key:
            settings.google_api_key = request.google.api_key
        if request.google.api_base:
            settings.google_api_base = request.google.api_base
    
    if request.azure:
        settings.azure_enabled = request.azure.enabled
        if request.azure.api_base:
            settings.azure_api_base = request.azure.api_base
        if request.azure.deployment_name:
            settings.azure_deployment_name = request.azure.deployment_name
        if request.azure.api_key:
            settings.azure_api_key = request.azure.api_key
        if request.azure.api_version:
            settings.azure_api_version = request.azure.api_version
    
    # Legacy settings support
    if request.api_style is not None:
        settings.api_style = request.api_style
    if request.enable_prefix_caching is not None:
        settings.enable_prefix_caching = request.enable_prefix_caching
    if request.enable_thinking is not None:
        settings.enable_thinking = request.enable_thinking
    
    # Handle legacy api_key/api_base (for backward compatibility)
    if request.api_key:
        settings.llm_api_key = request.api_key
        if not settings.openai_api_key:
            settings.openai_api_key = request.api_key
    if request.api_base:
        settings.llm_api_base = request.api_base
    
    # Determine which provider to use and get API key
    settings.default_provider = provider
    
    # Create agent with the selected provider
    print(f"[Init] Creating Agent with provider={provider}, model={settings.default_model}")
    
    _agent = NBCCAgent(
        provider=provider
    )
    
    print(f"[Init] Agent initialized successfully")
    return InitResponse(
        status="ok",
        message=f"Agent initialized with {provider} provider, model {settings.default_model}"
    )


# ==================== Chat ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint.
    Returns all results at once after completion.
    """
    agent = get_agent()
    
    results = []
    async for event in agent.chat(request.message):
        results.append(ChatResult(type=event["type"], data=event["data"]))
    
    return ChatResponse(results=results)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint (SSE).
    Returns events as they happen.
    """
    print(f"[Chat] Received message: {request.message[:100]}...")
    print(f"[Chat] Request model: {request.model}, mode: {request.mode}")
    print(f"[Chat] Current settings: api_style={settings.api_style}, model={settings.default_model}")
    
    agent = get_agent()
    
    # Override model if specified in request
    model_override = request.model if request.model else settings.default_model
    chat_mode = request.mode or "agent"
    
    print(f"[Chat] Using model: {model_override}, mode: {chat_mode}")
    print(f"[Chat] Agent api_base: {agent.api_base}")
    
    async def event_generator():
        try:
            print(f"[Chat] Starting chat_with_logs...")
            event_count = 0
            
            # Use different chat method based on mode
            if chat_mode == "chat":
                # Simple chat mode - no tools
                async for event in agent.simple_chat(request.message, model=model_override):
                    event_count += 1
                    event["timestamp"] = datetime.now().isoformat()
                    print(f"[Chat] Event #{event_count}: type={event.get('type')}")
                    yield f"data: {json.dumps(event)}\n\n"
            else:
                # Agent mode - with tools
                async for event in agent.chat_with_logs(request.message, model=model_override):
                    event_count += 1
                    event["timestamp"] = datetime.now().isoformat()
                    print(f"[Chat] Event #{event_count}: type={event.get('type')}")
                    yield f"data: {json.dumps(event)}\n\n"
                    
            print(f"[Chat] Finished. Total events: {event_count}")
        except Exception as e:
            import traceback
            print(f"[Chat] ERROR: {e}")
            print(f"[Chat] Traceback: {traceback.format_exc()}")
            error_event = {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ==================== Files ====================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    path: str = Query(default=None, description="Target directory path")
):
    """Upload a file to the virtual machine"""
    
    # Use default upload directory if not specified
    target_dir = path or settings.upload_dir
    
    # Ensure directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(target_dir, file.filename)
    
    content = await file.read()
    
    # Check file size
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.max_upload_size // 1024 // 1024}MB"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return FileUploadResponse(
        status="ok",
        path=file_path,
        filename=file.filename,
        size=len(content)
    )


@router.get("/download")
async def download_file(path: str = Query(..., description="File path to download")):
    """Download a file from the virtual machine"""
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    return FileResponse(
        path=path,
        filename=os.path.basename(path),
        media_type="application/octet-stream"
    )


@router.get("/files", response_model=FileListResponse)
async def list_files(path: str = Query(default=None, description="Directory path")):
    """List files in a directory"""
    
    target_path = path or settings.work_dir
    
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    files = []
    for entry in os.scandir(target_path):
        files.append({
            "name": entry.name,
            "path": entry.path,
            "is_dir": entry.is_dir(),
            "size": entry.stat().st_size if entry.is_file() else None,
            "modified": datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
        })
    
    return FileListResponse(path=target_path, files=files)


# ==================== History ====================

@router.get("/history", response_model=HistoryResponse)
async def get_history():
    """Get chat history"""
    agent = get_agent()
    return HistoryResponse(messages=agent.get_messages())


@router.post("/clear")
async def clear_history():
    """Clear chat history"""
    agent = get_agent()
    agent.clear_messages()
    return {"status": "ok", "message": "History cleared"}


# ==================== Control ====================

@router.post("/interrupt")
async def interrupt():
    """Interrupt current execution"""
    agent = get_agent()
    agent.interrupt()
    return {"status": "ok", "message": "Interrupt signal sent"}


# ==================== Health ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agent_initialized=_agent is not None,
        version="0.1.0"
    )

