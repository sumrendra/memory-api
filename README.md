# Memory API

A minimal FastAPI service that provides two endpoints to store and search memory chunks in Postgres with pgvector (rag.chunks).

Step 1 (DB prep) is assumed complete as per your setup. This service implements Step 2.

## Endpoints

- POST /memory/store
  - Body: { "doc_id": "<string>", "text": "<long text>", "meta": { ... optional ... } }
  - Splits text into chunks, embeds using the configured embedding provider, and upserts into rag.chunks.
  - Idempotent by doc_id: existing rows with the same doc_id are deleted and replaced.

- POST /memory/search
  - Body: { "query": "<string>", "top_k": 5, "filter": { ... optional exact-match on metadata ... } }
  - Embeds the query and returns top-k nearest chunks with cosine similarity.

- GET /health
  - Health check for service readiness.

- GET /config
  - Returns non-sensitive runtime configuration (embedding provider/model, schema/table, chunking, version).

## Run locally

1. Create a .env from the example and set DATABASE_URL. Choose embeddings provider via EMBEDDING_PROVIDER (default: huggingface). Ensure the embedding dimension matches your DB (VECTOR(768) by default in your table).

```
cp .env.example .env
# edit .env to match your Postgres and desired embeddings provider/model
```

2. Install dependencies and start the server:

```
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8081
```

3. Test quickly:

```
curl -s http://localhost:8081/config | jq
curl -s http://localhost:8081/health
curl -s -X POST http://localhost:8081/memory/store \
  -H 'Content-Type: application/json' \
  -d '{"doc_id":"demo1","text":"Alice lives in Wonderland. Bob lives in Paris.","meta":{"source":"demo"}}'

curl -s -X POST http://localhost:8081/memory/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Where does Bob live?","top_k":3,"filter":{"source":"demo"}}' | jq
```

## LM Studio wiring (model-agnostic)

- Define two tools in LM Studio pointing to this API (your LLM can be changed freely in LM Studio):
  - store_memory: POST http://<host>:8081/memory/store with body { doc_id, text, meta? }
  - recall_memory: POST http://<host>:8081/memory/search with body { query, top_k?, filter? }
- This API does not depend on the chat/generation model. You can switch LLMs in LM Studio without touching this API.

## Notes

- Default embeddings provider is HuggingFace with sentence-transformers/all-mpnet-base-v2 (dim 768). If you change provider/model (e.g., Ollama nomic-embed-text, or OpenAI text-embedding-3-small), ensure the DB column VECTOR(dim) matches.
- Dimension validation: GET /config validates that the embedding vector length, your configured VECTOR_DIM, and the DB column dimension all match. It returns 500 with details if mismatched so you can fix config before use.
- The service uses direct SQL with SQLAlchemy for store/search and pgvector cosine ops; schema/table can be controlled via env.
- For idempotency, /memory/store removes existing chunks with the same doc_id before insert.
- Semantic deduplication: /memory/store performs greedy cosine-based dedupe within a single request to avoid near-duplicate chunks. Configure via DEDUPE_ENABLED (default on) and DEDUPE_THRESHOLD (default 0.98).
- You can filter by metadata in /memory/search with exact matches (e.g., {"source": "web"}) and you can restrict to a specific doc_id by passing doc_id in the request.