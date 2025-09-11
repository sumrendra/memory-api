# 🧠 Streamlit Memory Chat Interface

A beautiful web interface for your Memory API with LM Studio integration.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install streamlit requests
```

### 2. Run the Interface
```bash
# Option 1: Use the launcher script
./run_streamlit.sh

# Option 2: Direct command  
streamlit run streamlit_chat.py
```

### 3. Open Your Browser
- Go to: `http://localhost:8501`
- Start chatting with memory-enabled AI!

## ✨ Features

### 🎨 **Beautiful Web Interface**
- Clean, modern design
- Real-time chat bubbles
- Sidebar with system status
- Memory operation indicators

### 🧠 **Smart Memory Integration**
- **Automatic Storage**: AI stores important info without being asked
- **Context Recall**: AI remembers previous conversations  
- **Visual Feedback**: See when memories are stored/retrieved
- **Recent Memories**: View stored information in sidebar

### 🔧 **System Monitoring**
- Memory API status indicator
- Recent memories browser
- Debug information panel
- Connection health checks

## 🎯 **How It Works**

1. **Natural Chat**: Just talk normally with the AI
2. **Auto Memory**: AI automatically stores important information
3. **Smart Recall**: AI pulls relevant context when needed
4. **Visual Feedback**: Memory operations shown in chat

## 💬 **Example Conversations**

**Storing Preferences:**
```
You: "I prefer Python over JavaScript for backend development"
AI: "Got it! I'll remember your programming language preferences."
🧠 Memory: ✅ Stored: User prefers Python over JavaScript for backend development
```

**Recalling Information:**
```
You: "What programming languages do I prefer?"
AI: "Based on what you told me before, you prefer Python over JavaScript for backend development."
🧠 Memory: 🔍 Found memories: User prefers Python over JavaScript...
```

## ⚙️ **Configuration**

### API Endpoints
Update these in `streamlit_chat.py` if needed:
```python
MEMORY_API_BASE = "http://192.168.1.4:8081"    # Your Memory API
LM_STUDIO_API = "http://192.168.1.14:1234/v1/chat/completions"  # Your LM Studio
```

### LLM Model
Update the model name in the chat function:
```python
"model": "qwen/qwen3-4b-2507"  # Change to your model
```

## 🛠️ **Troubleshooting**

### Memory API Not Connected
- Check if your Memory API is running: `curl http://192.168.1.4:8081/health`
- Verify the IP address in configuration
- Make sure port 8081 is accessible

### LM Studio Not Connected  
- Check if LM Studio is running with API enabled
- Verify the IP address and port (default: 1234)
- Make sure a model is loaded in LM Studio

### Installation Issues
```bash
# Install specific versions
pip install streamlit==1.37.0 requests==2.31.0

# Or install from requirements
pip install -r requirements.txt
```

## 🌟 **Advanced Features**

### Custom Styling
The interface includes custom CSS for beautiful chat bubbles and modern styling.

### Memory Categories
AI automatically categorizes memories:
- `personal` - Personal information
- `preference` - User preferences  
- `work` - Work-related info
- `schedule` - Time-based information
- `learning` - Educational content
- `general` - Everything else

### Persistence  
All memories are stored in your PostgreSQL database and persist across sessions.

## 🔄 **Next Steps**

This Streamlit interface is much more dynamic than CLI! You can:

1. **Deploy it**: Host on your server for remote access
2. **Mobile Friendly**: Access from any device with a browser
3. **Share**: Others can use the same interface
4. **Extend**: Add more features like file uploads, voice input, etc.

Enjoy your new web-based memory chat interface! 🎉