import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_vector_store, get_workflow
from app.config.settings import get_settings
from app.graph.workflow import MultiAgentWorkflow
from app.models import ChatRequest, ChatResponse, IngestRequest, IngestResponse
from app.rag.vector_store import VectorStoreService

router = APIRouter()

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".html",
    ".css",
}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": get_settings().app_name}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    workflow: MultiAgentWorkflow = Depends(get_workflow),
) -> ChatResponse:
    return await workflow.ainvoke(request.message, request.session_id)


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    workflow: MultiAgentWorkflow = Depends(get_workflow),
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for update in workflow.astream(request.message, request.session_id):
            yield f"data: {json.dumps(update, default=str)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/rag/ingest", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> IngestResponse:
    try:
        indexed = 0
        if request.texts:
            indexed += await vector_store.ingest_texts(request.texts, request.metadatas)
        if request.paths:
            indexed += await vector_store.ingest_paths(request.paths)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IngestResponse(
        indexed_documents=indexed,
        collection_name=get_settings().chroma_collection_name,
    )


@router.post("/rag/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> IngestResponse:
    filename = file.filename or "uploaded-document.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Upload a text-like file such as .txt, .md, "
                ".py, .js, .ts, .json, .csv, .yaml, .html, or .css."
            ),
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than the 2 MB upload limit.")

    try:
        indexed = await vector_store.ingest_file_content(
            filename=filename,
            content=content,
            content_type=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IngestResponse(
        indexed_documents=indexed,
        collection_name=get_settings().chroma_collection_name,
    )
