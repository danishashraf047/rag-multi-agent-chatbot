from functools import lru_cache

from app.config.settings import get_settings
from app.graph.workflow import MultiAgentWorkflow
from app.rag.vector_store import VectorStoreService


@lru_cache
def get_workflow() -> MultiAgentWorkflow:
    return MultiAgentWorkflow(get_settings())


@lru_cache
def get_vector_store() -> VectorStoreService:
    return VectorStoreService(get_settings())
