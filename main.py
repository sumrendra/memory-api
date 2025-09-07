import os
import hashlib
import json
from typing import Optional, List, Dict, Any

import numpy as np

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text, event

# Load environment variables from .env if present
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
# Support JDBC-style URL if provided (convert to SQLAlchemy/psycopg format)
if DATABASE_URL and DATABASE_URL.startswith("jdbc:postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("jdbc:postgresql://"):]
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

# Deduplication config (semantic dedupe within a single store request)
DEDUPE_ENABLED = os.getenv("DEDUPE_ENABLED", "1").lower() not in {"0", "false", "no"}
DEDUPE_THRESHOLD = float(os.getenv("DEDUPE_THRESHOLD", "0.98"))  # cosine similarity threshold

# PGVector settings
# We will use the existing schema/table created by Step 1
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chunks")  # logical collection label inside table
RAG_SCHEMA = os.getenv("RAG_SCHEMA", "rag")
TABLE_NAME = os.getenv("TABLE_NAME", "chunks")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "768"))
# Quote identifiers to be safe with any naming
QUALIFIED_TABLE = f'"{RAG_SCHEMA}"."{TABLE_NAME}"'
# Auto-create schema/table if missing (1/true to enable, 0/false to disable)
AUTO_CREATE = os.getenv("AUTO_CREATE", "1").lower() not in {"0", "false", "no"}

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
    doc_id: Optional[str] = Field(default=None, description="Optional doc_id exact match")


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


_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        # Ensure connections prefer the configured schema
        def _set_search_path(dbapi_connection, connection_record):
            try:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {RAG_SCHEMA}, public")
            except Exception:
                # Don't block startup if this fails; queries use qualified names
                pass

        try:
            event.listen(_engine, "connect", _set_search_path)
        except Exception:
            pass
    return _engine


_ensured_schema_and_table = False
def ensure_schema_and_table_exists():
    global _ensured_schema_and_table
    if _ensured_schema_and_table:
        return
    engine = get_engine()
    try:
        with engine.begin() as conn:
            if AUTO_CREATE:
                # Ensure pgvector extension exists (safe if already installed)
                try:
                    conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
                except Exception:
                    pass
                # Create schema/table/index if missing
                conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{RAG_SCHEMA}"')
                conn.exec_driver_sql(
                    f"CREATE TABLE IF NOT EXISTS {QUALIFIED_TABLE} ("
                    "id BIGSERIAL PRIMARY KEY, "
                    "doc_id TEXT NOT NULL, "
                    "chunk TEXT NOT NULL, "
                    "meta JSONB, "
                    f"embedding VECTOR({VECTOR_DIM})"
                    ")"
                )
                try:
                    conn.exec_driver_sql(
                        f"CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw "
                        f"ON {QUALIFIED_TABLE} USING hnsw (embedding vector_cosine_ops) "
                        "WITH (m = 16, ef_construction = 64)"
                    )
                except Exception:
                    pass
    except Exception:
        # If creation fails, continue; subsequent queries may still work if table exists
        pass
    _ensured_schema_and_table = True


def _to_pgvector_literal(vec: List[float]) -> str:
    # Format a Python list of floats into pgvector literal: [v1, v2, ...]
    # Keep a reasonable precision to avoid overly long SQL literals.
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def hash_chunk_id(doc_id: str, text: str) -> str:
    # Deterministic UUID-like string id for a chunk based on doc_id+content
    return hashlib.sha256(f"{doc_id}:::{text}".encode("utf-8")).hexdigest()


@app.get("/")
async def root():
    return {"message": "Memory API running", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    # Lightweight readiness check without initializing embeddings/DB
    return {"status": "ok"}


@app.get("/config")
async def config():
    # Return non-sensitive runtime configuration so LM Studio tools can introspect
    try:
        _ = get_embeddings()
        dim_status = validate_dims_or_raise()
    except HTTPException:
        # Propagate dimension mismatch as-is (500)
        raise
    except Exception as e:
        # Surface embedding initialization errors for easier troubleshooting
        raise HTTPException(status_code=500, detail=f"Embeddings init failed: {e}")

    # DB diagnostics to confirm where we're connected and which schema is active
    db_info: Dict[str, Any] = {}
    try:
        engine = get_engine()
        with engine.connect() as conn:
            db = conn.execute(text("select current_database()")).scalar_one()
            sch = conn.execute(text("select current_schema()")).scalar_one()
            spath = conn.execute(text("show search_path")).scalar_one()
            usr = conn.execute(text("select current_user")).scalar_one()
            db_info = {
                "current_database": db,
                "current_schema": sch,
                "search_path": spath,
                "current_user": usr,
                "qualified_table": f"{RAG_SCHEMA}.{TABLE_NAME}",
            }
    except Exception:
        pass

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
        "vector_dim": {
            "configured": VECTOR_DIM,
            "embedding": dim_status.get("embedding_dim"),
            "db": dim_status.get("db_vector_dim"),
            "match": dim_status.get("match"),
        },
        "dedupe": {"enabled": DEDUPE_ENABLED, "threshold": DEDUPE_THRESHOLD},
        "db": db_info,
        "version": "0.2.0"
    }


@app.get("/debug/peek")
async def debug_peek(doc_id: Optional[str] = None, limit: int = 5):
    # Quick view into recent rows to validate inserts are going to the expected place
    ensure_schema_and_table_exists()
    try:
        engine = get_engine()
        sql = f"SELECT id, doc_id, chunk, meta FROM {QUALIFIED_TABLE}"
        params: Dict[str, Any] = {"limit": limit}
        if doc_id:
            sql += " WHERE doc_id = :doc_id"
            params["doc_id"] = doc_id
        sql += " ORDER BY id DESC LIMIT :limit"
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        return {
            "table": f"{RAG_SCHEMA}.{TABLE_NAME}",
            "rows": [
                {
                    "id": int(r.id),
                    "doc_id": str(r.doc_id),
                    "chunk": str(r.chunk),
                    "meta": r.meta if isinstance(r.meta, dict) else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Peek failed: {e}")


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

    # Compute embeddings for all chunks
    try:
        embeddings = get_embeddings().embed_documents(texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    # Optional semantic deduplication within this batch (greedy, cosine similarity)
    kept_texts = []
    kept_embs = []
    if DEDUPE_ENABLED and embeddings:
        # Normalize embeddings for cosine similarity
        embs = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12
        embs_norm = embs / norms
        for idx, (t, e_norm) in enumerate(zip(texts, embs_norm)):
            if len(kept_embs) == 0:
                kept_texts.append(t)
                kept_embs.append(e_norm)
                continue
            sims = np.dot(np.vstack(kept_embs), e_norm)
            if float(np.max(sims)) >= DEDUPE_THRESHOLD:
                # Skip near-duplicate chunk
                continue
            kept_texts.append(t)
            kept_embs.append(e_norm)
        # Recompute embeddings literals based on original (unnormalized) vectors for kept indices
        # Map back kept indices by matching text order
        kept_set = set(kept_texts)
        filtered = [(t, e) for t, e in zip(texts, embeddings) if t in kept_set]
        texts = [t for t, _ in filtered]
        embeddings = [e for _, e in filtered]
    else:
        kept_texts = texts

    # Validate dimensions before writing
    _ = validate_dims_or_raise()

    # Upsert behavior: delete existing rows for this doc_id, then insert fresh chunks
    try:
        ensure_schema_and_table_exists()
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {QUALIFIED_TABLE} WHERE doc_id = :doc_id"), {"doc_id": req.doc_id})
            for chunk_text, embed in zip(texts, embeddings):
                embed_lit = _to_pgvector_literal(embed)
                conn.execute(
                    text(
                        f"INSERT INTO {QUALIFIED_TABLE} (doc_id, chunk, meta, embedding) "
                        f"VALUES (:doc_id, :chunk, CAST(:meta AS JSONB), CAST(:embedding AS vector({VECTOR_DIM})))"
                    ),
                    {
                        "doc_id": req.doc_id,
                        "chunk": chunk_text,
                        "meta": json.dumps(req.meta or {}),
                        "embedding": embed_lit,
                    },
                )
        # Verify how many rows were actually written for this doc_id in the connected DB/schema
        with engine.connect() as conn:
            stored_count = conn.execute(
                text(f"SELECT count(*) FROM {QUALIFIED_TABLE} WHERE doc_id = :doc_id"),
                {"doc_id": req.doc_id},
            ).scalar_one()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store chunks: {e}")

    return StoreResponse(doc_id=req.doc_id, chunks_inserted=int(stored_count))


@app.post("/memory/search", response_model=SearchResponse)
async def search_memory(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query is empty")

    # Validate dimensions before embedding/query
    _ = validate_dims_or_raise()

    # Compute query embedding
    try:
        q_embed = get_embeddings().embed_query(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    q_vec = _to_pgvector_literal(q_embed)

    # Build SQL with optional filters
    base_sql = (
        f"SELECT id, doc_id, chunk, meta, "
        f"(embedding <=> CAST(:q_vec AS vector({VECTOR_DIM}))) AS distance "
        f"FROM {QUALIFIED_TABLE}"
    )
    params = {"q_vec": q_vec, "k": req.top_k}
    conditions = []
    if req.filter:
        conditions.append("meta @> CAST(:filter AS JSONB)")
        params["filter"] = json.dumps(req.filter)
    if req.doc_id:
        conditions.append("doc_id = :doc_id")
        params["doc_id"] = req.doc_id
    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)
    base_sql += " ORDER BY distance ASC LIMIT :k"

    try:
        ensure_schema_and_table_exists()
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(base_sql), params).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    results: List[SearchChunk] = []
    for row in rows:
        # Convert distance to a descending "score" (higher is better)
        distance = float(row.distance)
        score = 1.0 - distance
        results.append(
            SearchChunk(
                id=int(row.id),
                doc_id=str(row.doc_id),
                chunk=str(row.chunk),
                meta=row.meta if isinstance(row.meta, dict) else None,
                score=score,
            )
        )

    return SearchResponse(query=req.query, results=results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8081")), reload=False)


# --- Embedding/DB dimension validation helpers ---
_embedding_dim_cache: Optional[int] = None
_db_vector_dim_cache: Optional[int] = None

def get_embedding_dim() -> int:
    global _embedding_dim_cache
    if _embedding_dim_cache is not None:
        return _embedding_dim_cache
    # Use a short probe string to get dimension
    vec = get_embeddings().embed_query("dimension check")
    _embedding_dim_cache = int(len(vec))
    return _embedding_dim_cache


def get_db_vector_dim() -> Optional[int]:
    """Inspect the DB to find the vector dimension of the embedding column."""
    global _db_vector_dim_cache
    if _db_vector_dim_cache is not None:
        return _db_vector_dim_cache
    try:
        ensure_schema_and_table_exists()
        engine = get_engine()
        sql = (
            "SELECT format_type(a.atttypid, a.atttypmod) as type_str "
            "FROM pg_attribute a "
            "JOIN pg_class c ON a.attrelid = c.oid "
            "JOIN pg_namespace n ON c.relnamespace = n.oid "
            "WHERE n.nspname = :schema AND c.relname = :table AND a.attname = 'embedding'"
        )
        with engine.connect() as conn:
            type_str = conn.execute(text(sql), {"schema": RAG_SCHEMA, "table": TABLE_NAME}).scalar()
        if type_str and isinstance(type_str, str) and type_str.startswith("vector("):
            try:
                dim = int(type_str[type_str.find("(") + 1:type_str.find(")")])
                _db_vector_dim_cache = dim
                return dim
            except Exception:
                return None
    except Exception:
        return None
    return None


def validate_dims_or_raise() -> Dict[str, Any]:
    emb_dim = get_embedding_dim()
    db_dim = get_db_vector_dim()
    expected = VECTOR_DIM
    status = {
        "embedding_dim": emb_dim,
        "db_vector_dim": db_dim,
        "configured_vector_dim": expected,
        "match": (db_dim == emb_dim == expected) if db_dim is not None else (emb_dim == expected),
    }
    if not status["match"]:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Embedding/DB dimension mismatch",
                "details": status,
                "hint": "Ensure EMBEDDING_MODEL_NAME matches VECTOR(dim) in your table and VECTOR_DIM env."
            }
        )
    return status
