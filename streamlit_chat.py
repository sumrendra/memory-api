import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import time
from typing import Dict, List, Any

# Configuration - Use environment variables for Docker deployment
import os

MEMORY_API_BASE = os.getenv("MEMORY_API_BASE", "http://192.168.1.4:8081")
LM_STUDIO_API = os.getenv("LM_STUDIO_API", "http://192.168.1.14:1234/v1/chat/completions")

# Page config
st.set_page_config(
    page_title="🧠 NeuroChat - AI Memory Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-Modern CSS with Glass morphism and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .main-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 25px 45px rgba(0, 0, 0, 0.1);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .neuro-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57);
        background-size: 400% 400%;
        animation: gradient-shift 8s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 2rem;
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
        margin-bottom: 2rem;
    }
    
    .message-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 25px 25px 8px 25px;
        margin: 1rem 0 1rem auto;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.3s ease-out;
    }
    
    .message-assistant {
        background: rgba(255, 255, 255, 0.95);
        color: #2c3e50;
        padding: 1rem 1.5rem;
        border-radius: 25px 25px 25px 8px;
        margin: 1rem auto 1rem 0;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        animation: slideInLeft 0.3s ease-out;
    }
    
    .message-memory {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 20px;
        margin: 0.5rem auto;
        font-size: 0.9rem;
        text-align: center;
        max-width: 60%;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    .status-online {
        background: linear-gradient(45deg, #4CAF50, #8BC34A);
        box-shadow: 0 0 10px #4CAF50;
    }
    
    .status-offline {
        background: linear-gradient(45deg, #f44336, #ff9800);
        box-shadow: 0 0 10px #f44336;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 5px currentColor; }
        to { box-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
    }
    
    .memory-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .memory-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.02);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .input-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .feature-badge {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    }
    
    .typing-indicator {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
    }
    
    .typing-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        margin: 0 2px;
        animation: typing 1.4s ease-in-out infinite;
    }
    
    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        color: white;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Advanced UI Components
def render_typing_indicator():
    """Animated typing indicator"""
    return """
    <div class="typing-indicator">
        🤖 AI is thinking...
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>  
        <span class="typing-dot"></span>
    </div>
    """

def render_status_badge(status: bool, label: str) -> str:
    """Render animated status badge"""
    icon = "🟢" if status else "🔴"
    css_class = "status-online" if status else "status-offline"
    return f"""
    <div style="display: flex; align-items: center; margin: 0.5rem 0;">
        <span class="status-indicator {css_class}"></span>
        <strong>{icon} {label}</strong>
    </div>
    """

def render_memory_stats(memories: List[Dict]) -> Dict:
    """Generate memory statistics"""
    if not memories:
        return {"total": 0, "categories": {}, "recent": 0}
    
    categories = {}
    recent_count = 0
    now = datetime.now()
    
    for memory in memories:
        meta = memory.get('meta', {})
        category = meta.get('category', 'general')
        categories[category] = categories.get(category, 0) + 1
        
        # Count memories from last 24 hours
        timestamp = meta.get('timestamp')
        if timestamp:
            try:
                mem_time = datetime.fromisoformat(timestamp.replace('Z', ''))
                if (now - mem_time).days < 1:
                    recent_count += 1
            except:
                pass
    
    return {
        "total": len(memories),
        "categories": categories,
        "recent": recent_count
    }

def render_feature_badges():
    """Render feature badges"""
    features = [
        "🧠 Neural Memory", "🚀 Real-time Chat", "📊 Analytics", 
        "🎨 Modern UI", "📱 Mobile Ready", "🔒 Secure", 
        "⚡ Fast Search", "🌐 Multi-device"
    ]
    
    badge_html = ""
    for feature in features:
        badge_html += f'<span class="feature-badge">{feature}</span>'
    
    return f'<div style="text-align: center; margin: 1rem 0;">{badge_html}</div>'

# Helper functions
def store_memory(text: str, doc_id: str = None, meta: dict = None) -> dict:
    """Store memory via API"""
    try:
        payload = {
            "doc_id": doc_id or str(uuid.uuid4())[:8],
            "text": text,
            "meta": meta or {}
        }
        # Increased timeout for container networking
        response = requests.post(f"{MEMORY_API_BASE}/memory/store", json=payload, timeout=60)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Memory API timeout - please try again"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to Memory API - check if service is running"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_memory(query: str, top_k: int = 5) -> dict:
    """Search memory via API"""
    try:
        payload = {"query": query, "top_k": top_k}
        # Increased timeout for container networking
        response = requests.post(f"{MEMORY_API_BASE}/memory/search", json=payload, timeout=60)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Memory API search timeout - please try again"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to Memory API - check if service is running"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_memory_api_status() -> dict:
    """Check if Memory API is accessible"""
    try:
        response = requests.get(f"{MEMORY_API_BASE}/health", timeout=30)
        response.raise_for_status()
        return {"success": True, "status": "online"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Memory API health check timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to Memory API"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def chat_with_llm(messages: list, tools: list = None) -> dict:
    """Chat with LM Studio LLM"""
    try:
        payload = {
            "model": "qwen/qwen3-4b-2507",  # Update this to your model
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        if tools:
            payload["tools"] = tools
            
        # Increased timeout for LLM response
        response = requests.post(LM_STUDIO_API, json=payload, timeout=120)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "LLM response timeout - please try again"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to LM Studio - check if service is running"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Tool definitions for LLM
MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "store_memory",
            "description": "Store important information shared by the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Information to remember"},
                    "category": {"type": "string", "description": "Category like 'personal', 'preference', 'work', 'schedule'"}
                },
                "required": ["content", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Search for relevant stored memories",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for memories"}
                },
                "required": ["query"]
            }
        }
    }
]

def execute_memory_tool(tool_name: str, arguments: dict) -> str:
    """Execute memory tools with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if tool_name == "store_memory":
                result = store_memory(
                    text=arguments["content"],
                    meta={
                        "category": arguments["category"],
                        "timestamp": datetime.now().isoformat(),
                        "source": "web_chat"
                    }
                )
                if result["success"]:
                    return f"✅ Stored: {arguments['content'][:100]}{'...' if len(arguments['content']) > 100 else ''}"
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    return f"❌ Failed to store memory after {max_retries} attempts: {result['error']}"
            
            elif tool_name == "recall_memory":
                result = search_memory(arguments["query"], top_k=3)
                if result["success"] and result["data"].get("results"):
                    memories = [r['chunk'] for r in result["data"]["results"][:3]]
                    return f"🔍 Found {len(memories)} memories: {'; '.join([m[:100] + '...' if len(m) > 100 else m for m in memories])}"
                else:
                    if attempt < max_retries - 1 and "timeout" in result.get("error", "").lower():
                        time.sleep(2)  # Wait before retry
                        continue
                    return f"🔍 No relevant memories found: {result.get('error', 'Unknown error')}"
                    
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return f"❌ Tool execution failed after {max_retries} attempts: {str(e)}"
    
    return "❌ Unknown tool"

# Initialize session state with advanced features
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.conversation_history = [{
        "role": "system",
        "content": """You are NeuroChat, an advanced AI assistant with persistent memory capabilities. 

AUTOMATICALLY use memory tools when:
- User shares personal info, preferences, or important facts → store_memory()
- User asks questions that need context from past conversations → recall_memory()

Be natural, engaging, and helpful. Don't announce memory operations.
Categories: 'personal', 'preference', 'work', 'schedule', 'learning', 'general', 'creative', 'technical'"""
    }]
    st.session_state.chat_mode = "smart"
    st.session_state.memory_filter = "all"
    st.session_state.typing = False
    st.session_state.total_messages = 0
    st.session_state.session_start = datetime.now()

# Ultra-Modern Header with animations
st.markdown("""
<div class="main-container">
    <div class="neuro-header">
        NeuroChat AI
    </div>
    <div style="text-align: center; color: rgba(255,255,255,0.8); margin-bottom: 2rem;">
        <h3>🧠 Advanced Memory-Enhanced AI Assistant</h3>
        <p>Experience the future of conversational AI with persistent memory</p>
    </div>
""", unsafe_allow_html=True)

# Feature badges
st.markdown(render_feature_badges(), unsafe_allow_html=True)

# Advanced Sidebar with Glass Morphism
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🎛️ **NeuroChat Control Center**")
    
    # System Status with animated indicators
    st.markdown("#### 🔗 **System Health**")
    memory_status = check_memory_api_status()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(render_status_badge(memory_status["success"], "Memory API"), unsafe_allow_html=True)
    with col2:
        # Quick LM Studio check
        try:
            lm_response = requests.get(f"{LM_STUDIO_API.replace('/chat/completions', '/models')}", timeout=3)
            lm_online = lm_response.status_code == 200
        except:
            lm_online = False
        st.markdown(render_status_badge(lm_online, "LM Studio"), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat Settings
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ **Chat Settings**")
    
    chat_mode = st.selectbox(
        "🤖 AI Mode",
        ["smart", "creative", "analytical", "casual"],
        index=0,
        help="Choose AI personality style"
    )
    st.session_state.chat_mode = chat_mode
    
    memory_auto = st.toggle("🧠 Auto Memory", value=True, help="Automatically store important information")
    response_length = st.selectbox("� Response Style", ["concise", "balanced", "detailed"], index=1)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Memory Analytics  
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 📊 **Memory Analytics**")
    
    # Get memory statistics
    if st.button("� Refresh Stats", use_container_width=True):
        with st.spinner("Analyzing memories..."):
            recent_memories = search_memory("", top_k=50)
            if recent_memories["success"]:
                memories = recent_memories["data"].get("results", [])
                stats = render_memory_stats(memories)
                
                # Display metrics in cards
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{stats['total']}</h3>
                        <p>Total Memories</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{stats['recent']}</h3>
                        <p>Recent (24h)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Category breakdown
                if stats['categories']:
                    st.markdown("**📂 Categories:**")
                    for category, count in stats['categories'].items():
                        st.markdown(f"• {category.title()}: {count}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Memory Browser
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### 🗃️ **Memory Browser**")
    
    search_term = st.text_input("🔍 Search Memories", placeholder="Enter search term...")
    memory_filter = st.selectbox("📂 Filter by Category", 
                                ["all", "personal", "preference", "work", "schedule", "learning", "general"])
    
    if st.button("🔍 Search", use_container_width=True) or search_term:
        query = search_term if search_term else ""
        memories_result = search_memory(query, top_k=10)
        
        if memories_result["success"] and memories_result["data"].get("results"):
            memories = memories_result["data"]["results"]
            
            for i, memory in enumerate(memories[:5]):
                meta = memory.get('meta', {})
                category = meta.get('category', 'general')
                
                # Skip if filter doesn't match
                if memory_filter != "all" and category != memory_filter:
                    continue
                    
                with st.expander(f"💭 {memory['chunk'][:50]}..."):
                    st.markdown(f"**Content:** {memory['chunk']}")
                    st.markdown(f"**Category:** {category.title()}")
                    st.markdown(f"**Relevance:** {memory['score']:.3f}")
                    st.markdown(f"**ID:** `{memory['doc_id']}`")
                    
                    if st.button(f"🗑️ Delete", key=f"del_{memory['id']}"):
                        st.warning("Delete feature coming soon!")
        else:
            st.info("🤷 No memories found")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Session Info
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("#### � **Session Stats**")
    
    session_duration = datetime.now() - st.session_state.session_start
    hours, remainder = divmod(session_duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    st.markdown(f"""
    • **Duration:** {hours:02d}:{minutes:02d}:{seconds:02d}  
    • **Messages:** {len(st.session_state.messages)}  
    • **Mode:** {st.session_state.chat_mode.title()}
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Ultra-Modern Chat Interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Welcome message for empty chat
if not st.session_state.messages:
    st.markdown("""
    <div class="glass-card" style="text-align: center; margin: 2rem 0;">
        <h2 style="color: white; margin-bottom: 1rem;">👋 Welcome to NeuroChat!</h2>
        <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
            I'm your AI assistant with advanced memory capabilities. Start a conversation and I'll remember everything important!
        </p>
        <div style="margin-top: 1rem;">
            <span class="feature-badge">💬 Natural Conversation</span>
            <span class="feature-badge">🧠 Persistent Memory</span>
            <span class="feature-badge">⚡ Instant Recall</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display chat history with modern styling
chat_placeholder = st.empty()

with chat_placeholder.container():
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="message-user">
                <strong>👤 You</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
        elif message["role"] == "assistant":
            st.markdown(f"""
            <div class="message-assistant">
                <strong>🤖 NeuroChat</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
        elif message["role"] == "memory":
            st.markdown(f"""
            <div class="message-memory">
                🧠 {message["content"]}
            </div>
            """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Advanced Chat Input with modern styling
st.markdown('<div class="input-container">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([6, 1, 1])

with col1:
    user_input = st.text_input(
        "💬 Message", 
        placeholder="Ask me anything... I'll remember it! 🧠",
        label_visibility="collapsed",
        key="chat_input"
    )

with col2:
    send_button = st.button("📤", help="Send message", use_container_width=True)

with col3:
    voice_button = st.button("🎤", help="Voice input (coming soon)", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Quick action buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💡 Ask about my preferences", use_container_width=True):
        user_input = "What do you know about my preferences?"
        send_button = True

with col2:
    if st.button("📅 What's my schedule?", use_container_width=True):
        user_input = "What do you know about my schedule?"
        send_button = True

with col3:
    if st.button("🎯 Surprise me!", use_container_width=True):
        user_input = "Tell me something interesting based on what you know about me"
        send_button = True

with col4:
    if st.button("🧠 Memory status", use_container_width=True):
        user_input = "How much do you remember about me?"
        send_button = True

if user_input and (send_button or st.session_state.get('auto_send', False)):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    # Show typing indicator
    typing_placeholder = st.empty()
    typing_placeholder.markdown(render_typing_indicator(), unsafe_allow_html=True)
    
    with st.spinner("� Processing with neural networks..."):
        time.sleep(0.5)  # Brief pause for UX
        
        # Enhanced system prompt based on chat mode
        enhanced_prompt = st.session_state.conversation_history[0]["content"]
        if st.session_state.chat_mode == "creative":
            enhanced_prompt += "\n\nBe creative, imaginative, and think outside the box."
        elif st.session_state.chat_mode == "analytical":
            enhanced_prompt += "\n\nBe analytical, logical, and provide detailed explanations."
        elif st.session_state.chat_mode == "casual":
            enhanced_prompt += "\n\nBe casual, friendly, and conversational."
        
        # Update system message temporarily
        temp_history = st.session_state.conversation_history.copy()
        temp_history[0]["content"] = enhanced_prompt
        
        # Get LLM response with memory tools
        llm_response = chat_with_llm(temp_history, MEMORY_TOOLS)
        
        # Clear typing indicator
        typing_placeholder.empty()
        
        if llm_response["success"]:
            message = llm_response["data"]["choices"][0]["message"]
            
            # Handle tool calls (memory operations)
            if message.get("tool_calls"):
                # Add assistant message with tool calls to conversation history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": message["tool_calls"]
                })
                
                # Execute memory operations
                memory_results = []
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    # Execute memory function
                    result = execute_memory_tool(tool_name, arguments)
                    memory_results.append(result)
                    
                    # Add tool result to conversation history
                    st.session_state.conversation_history.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call["id"]
                    })
                
                # Show memory operations to user
                for result in memory_results:
                    st.session_state.messages.append({"role": "memory", "content": result})
                
                # Get final response after memory operations
                final_response = chat_with_llm(st.session_state.conversation_history)
                if final_response["success"]:
                    final_content = final_response["data"]["choices"][0]["message"]["content"]
                    st.session_state.messages.append({"role": "assistant", "content": final_content})
                    st.session_state.conversation_history.append({"role": "assistant", "content": final_content})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "Sorry, I had trouble processing that."})
            else:
                # No memory operations, just regular response
                reply = message["content"]
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.conversation_history.append({"role": "assistant", "content": reply})
        else:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {llm_response['error']}"})
    
    # Refresh the page to show new messages
    st.rerun()

# Advanced Footer with Glass Morphism
st.markdown("</div>", unsafe_allow_html=True)  # Close main container

st.markdown("""
<div class="glass-card" style="margin-top: 2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div style="color: white;">
            <h4 style="margin: 0;">🧠 NeuroChat AI</h4>
            <p style="margin: 0; opacity: 0.8;">Powered by Advanced Memory Technology</p>
        </div>
        <div style="color: white; text-align: right;">
            <p style="margin: 0; opacity: 0.8;">Session: {}</p>
            <p style="margin: 0; opacity: 0.6;">Messages: {}</p>
        </div>
    </div>
</div>
""".format(
    st.session_state.session_start.strftime("%H:%M:%S"),
    len(st.session_state.messages)
), unsafe_allow_html=True)

# Control Panel
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = [st.session_state.conversation_history[0]]
        st.session_state.total_messages = 0
        st.success("✅ Chat cleared!")
        time.sleep(1)
        st.rerun()

with col2:
    if st.button("📊 Export Chat", use_container_width=True):
        chat_export = {
            "session_start": st.session_state.session_start.isoformat(),
            "messages": st.session_state.messages,
            "total_messages": len(st.session_state.messages)
        }
        st.download_button(
            "💾 Download JSON",
            data=json.dumps(chat_export, indent=2),
            file_name=f"neurochat_session_{st.session_state.session_start.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

with col3:
    if st.button("� Restart", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

with col4:
    if st.button("🎨 Theme", use_container_width=True):
        st.info("🎨 Theme customization coming soon!")

with col5:
    if st.button("ℹ️ About", use_container_width=True):
        st.markdown("""
        ### 🧠 NeuroChat AI v2.0
        
        **Features:**
        - 🧠 Advanced persistent memory
        - 🎨 Modern glass morphism UI
        - 📱 Mobile responsive design
        - ⚡ Real-time chat with animations
        - 📊 Memory analytics and insights
        - 🎛️ Customizable AI personality
        - 🔍 Intelligent memory search
        - 💾 Session export/import
        
        **Tech Stack:**
        - Streamlit + Custom CSS
        - LM Studio Integration
        - PostgreSQL Vector Database
        - Advanced Memory API
        """)

# Hidden debug panel (toggle with secret combination)
if st.session_state.get('debug_mode', False):
    with st.expander("🔧 Debug Panel"):
        st.json({
            "session_state_keys": list(st.session_state.keys()),
            "messages_count": len(st.session_state.messages),
            "conversation_length": len(st.session_state.conversation_history),
            "memory_api": MEMORY_API_BASE,
            "llm_api": LM_STUDIO_API,
            "chat_mode": st.session_state.chat_mode,
            "session_duration": str(datetime.now() - st.session_state.session_start)
        })

# Enable debug mode with secret key combo
if st.text_input("🔐 Debug Key", type="password") == "neurochat_debug_2024":
    st.session_state.debug_mode = True
    st.success("🔧 Debug mode enabled!")