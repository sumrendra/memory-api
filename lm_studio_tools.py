# lm_studio_tools.py - Tools for LM Studio integration with Memory API

import json
import uuid
from typing import Dict, Any, Optional

# Update this to your server IP and port
MEMORY_API_BASE = "http://192.168.1.4:8081"

def store_memory(text: str, doc_id: str = None, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store text in memory system using the Memory API"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "requests module not available"}
    
    # Generate a unique doc_id if not provided
    if doc_id is None:
        doc_id = str(uuid.uuid4())
    
    payload = {
        "doc_id": doc_id,
        "text": text,
        "meta": meta or {}
    }

    try:
        response = requests.post(f"{MEMORY_API_BASE}/memory/store", json=payload)
        response.raise_for_status()
        result = response.json()
        return {
            "success": True,
            "doc_id": result["doc_id"],
            "chunks_inserted": result["chunks_inserted"],
            "message": f"Successfully stored {result['chunks_inserted']} chunks for document {result['doc_id']}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to store memory: {str(e)}"}

def recall_memory(query: str, top_k: int = 5, filter_meta: Dict[str, Any] = None, doc_id: str = None) -> Dict[str, Any]:
    """Search and recall memories from the Memory API"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "requests module not available"}
    
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    # Add optional filters
    if filter_meta:
        payload["filter"] = filter_meta
    if doc_id:
        payload["doc_id"] = doc_id

    try:
        response = requests.post(f"{MEMORY_API_BASE}/memory/search", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Format the response for better readability
        formatted_results = []
        for chunk in result["results"]:
            formatted_results.append({
                "id": chunk["id"],
                "doc_id": chunk["doc_id"],
                "content": chunk["chunk"],
                "metadata": chunk["meta"],
                "relevance_score": round(chunk["score"], 3)
            })
        
        return {
            "success": True,
            "query": result["query"],
            "total_results": len(formatted_results),
            "results": formatted_results
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to search memory: {str(e)}"}

def check_memory_api_status() -> Dict[str, Any]:
    """Check if the Memory API is running and get configuration info"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "requests module not available"}
        
    try:
        # Check health endpoint
        health_response = requests.get(f"{MEMORY_API_BASE}/health", timeout=5)
        health_response.raise_for_status()
        
        # Get configuration info
        config_response = requests.get(f"{MEMORY_API_BASE}/config", timeout=10)
        config_response.raise_for_status()
        config = config_response.json()
        
        return {
            "success": True,
            "status": "Memory API is running",
            "embedding_provider": config.get("embedding_provider"),
            "embedding_model": config.get("embedding_model_name"),
            "vector_dimension": config.get("vector_dim", {}).get("configured"),
            "version": config.get("version")
        }
    except Exception as e:
        return {"success": False, "error": f"Memory API not accessible: {str(e)}"}

# LM Studio tool definitions matching the actual API
LM_STUDIO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "store_memory",
            "description": "Store information in long-term memory. The text will be automatically chunked and embedded for efficient retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text content to store in memory. Can be any length - it will be automatically chunked."
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional unique identifier for this document. If not provided, a UUID will be generated. Use the same doc_id to update/replace existing content."
                    },
                    "meta": {
                        "type": "object",
                        "description": "Optional metadata to associate with this memory (e.g., {'category': 'conversation', 'date': '2024-01-01', 'tags': ['important']})"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Search and retrieve relevant memories based on a query. Returns the most similar stored content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of most relevant results to return (1-100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 5
                    },
                    "filter_meta": {
                        "type": "object",
                        "description": "Optional metadata filter to narrow results (exact match, e.g., {'category': 'conversation'})"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID to search within a specific document only"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_memory_api_status",
            "description": "Check if the Memory API is running and get its configuration. Use this to verify the system is working.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def main():
    """Print the tool definitions for LM Studio"""
    print("=== Memory API Tools for LM Studio ===\n")
    
    print(f"📡 API base URL: {MEMORY_API_BASE}")
    print("   Update MEMORY_API_BASE in this file if your API runs elsewhere.\n")
    
    print("💡 Make sure your Memory API is running:")
    print("   docker-compose up -d")
    print("   Then test with: curl http://192.168.1.4:8081/health\n")
    
    print("🔧 Copy the following JSON to LM Studio Tools configuration:")
    print("=" * 60)
    print(json.dumps(LM_STUDIO_TOOLS, indent=2))
    print("=" * 60)
    
    print("\n📝 Usage Examples:")
    print("   - store_memory('Important conversation about project X', meta={'type': 'meeting'})")
    print("   - recall_memory('project X details', top_k=3)")
    print("   - check_memory_api_status()")

if __name__ == "__main__":
    main()
