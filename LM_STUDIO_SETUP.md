# LM Studio Integration Guide

This file provides tools for integrating your Memory API with LM Studio, allowing any LLM to store and retrieve long-term memories.

## Quick Setup

1. **Start your Memory API:**
   ```bash
   docker-compose up -d
   ```

2. **Verify it's running:**
   ```bash
   curl http://192.168.1.4:8081/health
   ```

3. **Get the tool definitions:**
   ```bash
   python3 lm_studio_tools.py
   ```

4. **Copy the JSON output to LM Studio:**
   - Open LM Studio
   - Go to Tools/Functions configuration
   - Paste the JSON from step 3

## Available Tools

### 1. `store_memory`
Store information in long-term memory:
```python
store_memory(
    text="Important conversation about project details...",
    doc_id="project-meeting-2024-01-01",  # Optional
    meta={"category": "meeting", "project": "memory-api"}  # Optional
)
```

### 2. `recall_memory`
Search and retrieve relevant memories:
```python
recall_memory(
    query="project details from meetings",
    top_k=5,  # Number of results
    filter_meta={"category": "meeting"},  # Optional filter
    doc_id="specific-document"  # Optional: search within specific doc
)
```

### 3. `check_memory_api_status`
Verify the API is working:
```python
check_memory_api_status()
```

## Configuration

### Change API URL
If your Memory API runs on a different host/port, update the `MEMORY_API_BASE` variable in `lm_studio_tools.py`:

```python
MEMORY_API_BASE = "http://192.168.1.4:8081"  # Current setting
```

### Memory API Configuration
Your Memory API supports various embedding providers:
- **HuggingFace** (default): `sentence-transformers/all-mpnet-base-v2`
- **Ollama**: Local models like `nomic-embed-text`
- **OpenAI**: `text-embedding-3-small`

Configure via environment variables in your `.env` file.

## Usage in LM Studio

Once configured, you can ask the LLM to use memory naturally:

**User:** "Remember that I prefer Python over JavaScript for backend development"
**LLM:** I'll store that preference for you.
*[Uses store_memory tool]*

**User:** "What programming language do I prefer for backend?"
**LLM:** Let me check your preferences.
*[Uses recall_memory tool]*

## Features

- **Automatic Chunking**: Long texts are automatically split into manageable chunks
- **Semantic Search**: Uses embeddings for intelligent content retrieval
- **Metadata Filtering**: Organize memories with custom metadata
- **Upsert Logic**: Use the same `doc_id` to update existing content
- **Deduplication**: Automatically removes near-duplicate content

## Troubleshooting

### API Not Accessible
```bash
# Check if container is running
docker ps

# Check logs
docker-compose logs memory-api

# Restart if needed
docker-compose restart memory-api
```

### Connection Issues
- Verify the API URL in `MEMORY_API_BASE`
- Check firewall settings if using remote server
- Ensure port 8081 is accessible

### Python Dependencies
The tools require the `requests` library:
```bash
pip install requests
```

## Example Conversation Flow

1. **Store a memory:**
   ```
   User: "Remember that my favorite debugging technique is using print statements"
   LLM: [Calls store_memory] I've stored your debugging preference.
   ```

2. **Recall later:**
   ```
   User: "What's my preferred way to debug code?"
   LLM: [Calls recall_memory] Based on what you told me before, your favorite debugging technique is using print statements.
   ```

3. **Check system status:**
   ```
   User: "Is the memory system working?"
   LLM: [Calls check_memory_api_status] Yes, the memory system is running properly with HuggingFace embeddings.
   ```
