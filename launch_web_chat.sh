#!/bin/bash

echo "🧠 Memory Chat - Streamlit Interface"
echo "=================================="
echo ""

# Check system status
echo "📡 System Status:"

# Memory API Check
if curl -s http://192.168.1.4:8081/health > /dev/null 2>&1; then
    echo "✅ Memory API: Online at http://192.168.1.4:8081"
else
    echo "❌ Memory API: Offline at http://192.168.1.4:8081"
fi

# LM Studio Check  
if curl -s http://192.168.1.14:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LM Studio: Online at http://192.168.1.14:1234"
else
    echo "❌ LM Studio: Offline at http://192.168.1.14:1234"
fi

echo ""
echo "🚀 Starting Web Interface..."
echo "📱 Open your browser and go to:"
echo "   🏠 Local:   http://localhost:8501"
echo "   🌐 Network: http://192.168.1.14:8501"
echo ""
echo "💡 Features:"
echo "   • Beautiful web chat interface"
echo "   • Automatic memory storage/recall"  
echo "   • Real-time system status"
echo "   • Memory browser in sidebar"
echo "   • Works on mobile devices"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Launch Streamlit
/Users/sumrendra/Library/Python/3.9/bin/streamlit run streamlit_chat.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --browser.gatherUsageStats false