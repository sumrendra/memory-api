#!/bin/bash

echo "🔧 NeuroChat Quick Fix & Deploy"
echo "==============================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose not found!"
    exit 1
fi

print_status "Using Docker Compose: $COMPOSE_CMD"

# Step 1: Clean up any existing containers
print_status "Cleaning up existing containers..."
$COMPOSE_CMD down 2>/dev/null || true
docker system prune -f

# Step 2: Test database connection first
print_status "Testing database connection..."
if docker run --rm postgres:13 psql "postgresql://admin:epaps0991g@192.168.1.4:5432/appdb" -c "SELECT 1;" &>/dev/null; then
    print_success "Database connection successful"
else
    print_error "Database connection failed. Please check:"
    echo "  - PostgreSQL is running on 192.168.1.4:5432"
    echo "  - Database 'appdb' exists"
    echo "  - Credentials: admin/epaps0991g"
    exit 1
fi

# Step 3: Try simple deployment first (just memory-api)
print_status "Deploying memory-api only first..."
$COMPOSE_CMD -f docker-compose.simple.yml up --build -d memory-api

# Wait for it to start
sleep 30

# Check if it's healthy
print_status "Checking memory-api health..."
for i in {1..10}; do
    if curl -f -s http://localhost:8081/health &>/dev/null; then
        print_success "Memory API is healthy!"
        break
    else
        echo -n "."
        sleep 5
    fi
    
    if [ $i -eq 10 ]; then
        print_error "Memory API failed to start. Checking logs..."
        $COMPOSE_CMD -f docker-compose.simple.yml logs memory-api
        exit 1
    fi
done

# Step 4: Deploy UI if API is working
print_status "Deploying NeuroChat UI..."
$COMPOSE_CMD -f docker-compose.simple.yml up --build -d neurochat-ui

# Wait for UI to start
sleep 20

# Check UI health
print_status "Checking UI health..."
for i in {1..5}; do
    if curl -f -s http://localhost:8502/_stcore/health &>/dev/null; then
        print_success "NeuroChat UI is healthy!"
        break
    else
        echo -n "."
        sleep 10
    fi
done

echo ""
print_success "🎉 Deployment Complete!"
echo ""
echo "📱 Access your NeuroChat system:"
echo "   • NeuroChat UI: http://192.168.1.4:8502"
echo "   • Memory API:   http://192.168.1.4:8081"
echo "   • API Docs:     http://192.168.1.4:8081/docs"
echo ""
echo "🔧 Management commands:"
echo "   • View logs:    $COMPOSE_CMD -f docker-compose.simple.yml logs -f"
echo "   • Stop system:  $COMPOSE_CMD -f docker-compose.simple.yml down"
echo "   • Restart:      $COMPOSE_CMD -f docker-compose.simple.yml restart"
echo ""

# Show container status
$COMPOSE_CMD -f docker-compose.simple.yml ps