# Sample Knowledge Base Document

This file is a small sample document for testing the RAG ingestion flow.

LangGraph is used in this project to orchestrate a multi-agent workflow. The Supervisor Agent classifies the user's request and routes it to a specialized agent such as Planning, Research, Coding, or RAG.

FastAPI serves both the backend API and the browser UI. The API exposes chat, streaming chat, health check, and RAG ingestion endpoints.

ChromaDB stores embedded document chunks for retrieval augmented generation. After ingesting this file, ask the system:

```text
Using the knowledge base, what does LangGraph do in this project?
```
