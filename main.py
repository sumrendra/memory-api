import os
import hashlib
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector

# Load environment variables from .env if present
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Allow separate components as fallback
    pg_user = os.getenv("POSTGRES_USER", "admin")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "password")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "app")
    DATABASE_URL = f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

# Embeddings config (independent of any chat LLM). You can switch providers without code changes.
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()  # huggingface | ollama | openai
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")  # ensure dim matches DB
# Optional provider-specific params
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Text splitter config
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# PGVector settings
# We will use the existing schema/table created by Step 1
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chunks")  # logical collection label inside table
RAG_SCHEMA = os.getenv("RAG_SCHEMA", "rag")
TABLE_NAME = os.getenv("TABLE_NAME", "chunks")

# FastAPI
app = FastAPI(title="Memory API", version="0.2.0")


class StoreRequest(BaseModel):
    doc_id: str = Field(..., description="Document identifier used for upsert logic")
    text: str = Field(..., description="Raw text to chunk and store")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Optional JSON metadata")


class StoreResponse(BaseModel):
    doc_id: str
    chunks_inserted: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=100)
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata exact-match filter")


class SearchChunk(BaseModel):
    id: int
    doc_id: str
    chunk: str
    meta: Optional[Dict[str, Any]]
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchChunk]


# Initialize embeddings and vector store lazily
_embeddings = None
_vectorstore = None
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", ".", " "]
)


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        if EMBEDDING_PROVIDER == "huggingface":
            _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        elif EMBEDDING_PROVIDER == "ollama":
            # Requires local Ollama with an embedding-capable model pulled
            _embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
        elif EMBEDDING_PROVIDER == "openai":
            try:
                from langchain_openai import OpenAIEmbeddings
            except Exception as e:
                raise RuntimeError(f"OpenAI embeddings not available: {e}")
            if not OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY not set")
            _embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
        else:
            raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
    return _embeddings


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        # Use the existing rag.chunks table. PGVector from langchain-postgres supports specifying table/schema.
        _vectorstore = PGVector(
            embeddings=get_embeddings(),
            collection_name=COLLECTION_NAME,
            connection=DATABASE_URL,
            use_jsonb=True,
            table_name=TABLE_NAME,
            schema=RAG_SCHEMA,
            # distance strategy defaults to cosine for pgvector ops
        )
    return _vectorstore


def hash_chunk_id(doc_id: str, text: str) -> str:
    # Deterministic UUID-like string id for a chunk based on doc_id+content
    return hashlib.sha256(f"{doc_id}:::{text}".encode("utf-8")).hexdigest()


@app.get("/health")
async def health():
    # Simple connectivity check
    try:
        vs = get_vectorstore()
        # Postgres connectivity will be validated lazily; do a no-op
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def config():
    # Return non-sensitive runtime configuration so LM Studio tools can introspect
    try:
        _ = get_embeddings()
    except Exception as e:
        # Surface embedding initialization errors for easier troubleshooting
        raise HTTPException(status_code=500, detail=f"Embeddings init failed: {e}")
    return {
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model_name": EMBEDDING_MODEL_NAME if EMBEDDING_PROVIDER == "huggingface" else (
            OLLAMA_EMBEDDING_MODEL if EMBEDDING_PROVIDER == "ollama" else OPENAI_EMBEDDING_MODEL
        ),
        "schema": RAG_SCHEMA,
        "table": TABLE_NAME,
        "collection_name": COLLECTION_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "version": "0.2.0"
    }


@app.post("/memory/store", response_model=StoreResponse)
async def store_memory(req: StoreRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    # Split into chunks
    splits = _text_splitter.split_text(req.text)

    if not splits:
        return StoreResponse(doc_id=req.doc_id, chunks_inserted=0)

    # LangChain PGVector prefers list of Documents; but it can also accept texts with metadatas
    texts = splits
    # Metadata per chunk: include doc_id and provided meta
    base_meta = req.meta or {}
    metadatas = [{"doc_id": req.doc_id, **base_meta} for _ in texts]

    vs = get_vectorstore()

    # Idempotent upsert: delete existing rows for doc_id, then add all chunks
    # PGVector exposes delete where filter={'doc_id': ...} when metadata stored in jsonb
    try:
        vs.delete(filter={"doc_id": req.doc_id})
    except Exception:
        # If delete fails (e.g., no existing), continue
        pass

    # Generate deterministic IDs for chunks to avoid duplicates within this batch
    ids = [hash_chunk_id(req.doc_id, t) for t in texts]

    try:
        vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store chunks: {e}")

    return StoreResponse(doc_id=req.doc_id, chunks_inserted=len(texts))


@app.post("/memory/search", response_model=SearchResponse)
async def search_memory(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query is empty")

    vs = get_vectorstore()

    # Perform similarity search with score
    try:
        # Optionally apply an exact-match metadata filter
        docs_and_scores = vs.similarity_search_with_score(
            req.query,
            k=req.top_k,
            filter=req.filter or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    results: List[SearchChunk] = []
    for doc, score in docs_and_scores:
        # PGVector returns LC Document with page_content and metadata
        meta = doc.metadata or {}
        results.append(
            SearchChunk(
                id=int(meta.get("id")) if isinstance(meta.get("id"), (int, str)) and str(meta.get("id")).isdigit() else -1,
                doc_id=str(meta.get("doc_id", "")),
                chunk=doc.page_content,
                meta={k: v for k, v in meta.items() if k not in {"id", "doc_id"}},
                score=float(score),
            )
        )

    return SearchResponse(query=req.query, results=results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8081")), reload=False)
