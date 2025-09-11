#!/bin/bash

# Streamlit Memory Chat Launcher
echo "🧠 Starting Memory Chat Interface..."

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected"
    echo "Consider running: python3 -m venv venv && source venv/bin/activate"
fi

# Install requirements if needed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit and dependencies..."
    pip install streamlit requests
fi

# Check if Memory API is accessible
echo "🔍 Checking Memory API..."
if curl -s http://192.168.1.4:8081/health > /dev/null; then
    echo "✅ Memory API is online"
else
    echo "❌ Memory API not accessible at http://192.168.1.4:8081"
    echo "   Make sure your Memory API is running on the server"
fi

# Check if LM Studio is accessible  
echo "🔍 Checking LM Studio..."
if curl -s http://192.168.1.14:1234/v1/models > /dev/null; then
    echo "✅ LM Studio is online"
else
    echo "❌ LM Studio not accessible at http://192.168.1.14:1234"
    echo "   Make sure LM Studio is running with API enabled"
fi

echo ""
echo "🚀 Launching Streamlit app..."
echo "📱 Web interface will open at: http://localhost:8501"
echo ""

# Launch Streamlit
streamlit run streamlit_chat.py --server.port 8501 --server.headless false