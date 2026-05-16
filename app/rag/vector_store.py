from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import Settings


class VectorStoreService:
    """ChromaDB-backed vector store for retrieval augmented generation."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embeddings and RAG.")
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self.store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(settings.chroma_persist_dir),
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
        )

    async def ingest_texts(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        documents = [
            Document(page_content=text, metadata=(metadatas or [{}] * len(texts))[idx])
            for idx, text in enumerate(texts)
        ]
        chunks = self.splitter.split_documents(documents)
        if chunks:
            await self.store.aadd_documents(chunks)
        return len(chunks)

    async def ingest_paths(self, paths: list[str]) -> int:
        documents: list[Document] = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"Document not found: {raw_path}")
            text = path.read_text(encoding="utf-8", errors="ignore")
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": str(path), "title": path.name},
                ),
            )
        chunks = self.splitter.split_documents(documents)
        if chunks:
            await self.store.aadd_documents(chunks)
        return len(chunks)

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        return await self.store.asimilarity_search(query, k=k)
