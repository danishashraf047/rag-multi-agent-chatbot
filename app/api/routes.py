import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_vector_store, get_workflow
from app.config.settings import get_settings
from app.graph.workflow import MultiAgentWorkflow
from app.models import ChatRequest, ChatResponse, IngestRequest, IngestResponse
from app.rag.vector_store import VectorStoreService

router = APIRouter()


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
