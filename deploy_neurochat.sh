#!/bin/bash

echo "🚀 NeuroChat Memory System - Docker Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is ready"

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

print_success "Docker Compose found: $COMPOSE_CMD"

# Stop existing containers
print_status "Stopping existing containers..."
$COMPOSE_CMD down 2>/dev/null || true

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    print_status "Pulling latest changes from repository..."
    git pull origin main || print_warning "Failed to pull latest changes"
fi

# Build and start services
print_status "Building and starting services..."
$COMPOSE_CMD up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    print_status "Checking $service_name health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to become healthy"
    return 1
}

# Check Memory API health
if check_service_health "Memory API" "http://localhost:8081/health"; then
    MEMORY_API_HEALTHY=true
else
    MEMORY_API_HEALTHY=false
fi

# Check NeuroChat UI health  
if check_service_health "NeuroChat UI" "http://localhost:8502/_stcore/health"; then
    NEUROCHAT_UI_HEALTHY=true
else
    NEUROCHAT_UI_HEALTHY=false
fi

echo ""
echo "=============================================="
echo "🎉 Deployment Complete!"
echo "=============================================="

# Display service status
echo ""
echo "📊 Service Status:"
if [ "$MEMORY_API_HEALTHY" = true ]; then
    print_success "Memory API: http://localhost:8081"
    print_success "  ├─ Health: http://localhost:8081/health"
    print_success "  ├─ Config: http://localhost:8081/config"
    print_success "  └─ Docs: http://localhost:8081/docs"
else
    print_error "Memory API: Failed to start"
fi

if [ "$NEUROCHAT_UI_HEALTHY" = true ]; then
    print_success "NeuroChat UI: http://localhost:8502"
    print_success "  ├─ Local: http://localhost:8502"
    print_success "  └─ Network: http://192.168.1.4:8502"
else
    print_error "NeuroChat UI: Failed to start"
fi

echo ""
echo "🔧 Management Commands:"
echo "  View logs:     $COMPOSE_CMD logs -f"
echo "  Stop services: $COMPOSE_CMD down"
echo "  Restart:       $COMPOSE_CMD restart"
echo "  Update:        ./deploy_neurochat.sh"

echo ""
echo "💡 Quick Start:"
echo "  1. Open http://localhost:8502 in your browser"
echo "  2. Start chatting with NeuroChat AI"
echo "  3. Your conversations will be remembered!"

echo ""
echo "🛠️ Troubleshooting:"
if [ "$MEMORY_API_HEALTHY" = false ]; then
    echo "  Memory API issues:"
    echo "    - Check logs: $COMPOSE_CMD logs memory-api"
    echo "    - Verify database connection in docker-compose.yml"
    echo "    - Ensure PostgreSQL is accessible"
fi

if [ "$NEUROCHAT_UI_HEALTHY" = false ]; then
    echo "  NeuroChat UI issues:"
    echo "    - Check logs: $COMPOSE_CMD logs neurochat-ui"
    echo "    - Verify Memory API is running"
    echo "    - Check LM Studio connection"
fi

echo ""
echo "🌟 Features Available:"
echo "  ✅ Modern glass morphism UI"
echo "  ✅ Persistent memory system"
echo "  ✅ Real-time chat interface"
echo "  ✅ Memory analytics & search"
echo "  ✅ Multiple AI personality modes"
echo "  ✅ Session export/import"
echo "  ✅ Mobile responsive design"
echo "  ✅ Docker containerized deployment"

# Show container status
echo ""
echo "🐳 Container Status:"
$COMPOSE_CMD ps

# Optional: Open browser
if command -v open &> /dev/null && [ "$NEUROCHAT_UI_HEALTHY" = true ]; then
    read -p "🌐 Open NeuroChat UI in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:8502
    fi
fi