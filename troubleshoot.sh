#!/bin/bash

echo "🔍 NeuroChat Memory System - Troubleshooting"
echo "============================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
print_status "Step 1: Checking Docker setup..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running!"
    exit 1
fi
print_success "Docker is running"

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose not found!"
    exit 1
fi
print_success "Docker Compose found: $COMPOSE_CMD"

echo ""
print_status "Step 2: Testing database connection..."

# Test database connection
DB_TEST=$(docker run --rm postgres:13 psql "postgresql://admin:epaps0991g@192.168.1.4:5432/appdb" -c "SELECT 1;" 2>&1)
if echo "$DB_TEST" | grep -q "1 row"; then
    print_success "Database connection successful"
else
    print_error "Database connection failed:"
    echo "$DB_TEST"
    print_warning "Please check your database credentials and network connectivity"
fi

echo ""
print_status "Step 3: Stopping existing containers..."
$COMPOSE_CMD down 2>/dev/null || true

echo ""
print_status "Step 4: Building memory-api container with debug mode..."

# Build just the memory-api for debugging
$COMPOSE_CMD -f docker-compose.debug.yml up --build memory-api-debug

echo ""
print_status "Step 5: Checking logs..."
$COMPOSE_CMD -f docker-compose.debug.yml logs memory-api-debug

echo ""
print_status "Step 6: Testing manual startup..."

# Try to run the app manually in container
docker run --rm -it \
  -e DATABASE_URL="postgresql://admin:epaps0991g@192.168.1.4:5432/appdb" \
  -e EMBEDDING_PROVIDER="huggingface" \
  -e VECTOR_DIM="768" \
  -p 8081:8081 \
  $(docker images -q | head -1) \
  python -c "
import sys
print('Python version:', sys.version)
print('Current directory contents:')
import os
print(os.listdir('.'))
print('Trying to import memory-api...')
try:
    exec(open('memory-api.py').read())
    print('SUCCESS: memory-api.py loaded')
except Exception as e:
    print('ERROR loading memory-api.py:', e)
    import traceback
    traceback.print_exc()
"

echo ""
print_warning "If you see errors above, here are common solutions:"
echo ""
echo "1. 📁 File naming issues:"
echo "   - Ensure memory-api.py exists in repository"
echo "   - Check if the main app variable is named 'app'"
echo ""
echo "2. 🗄️ Database connection issues:"
echo "   - Verify PostgreSQL is running on 192.168.1.4:5432"
echo "   - Check username/password: admin/epaps0991g"
echo "   - Test database access from your server"
echo ""
echo "3. 🐳 Docker build issues:"
echo "   - Check Dockerfile syntax"
echo "   - Verify all required files are in repository"
echo "   - Check requirements.txt for missing dependencies"
echo ""
echo "4. 🌐 Network issues:"
echo "   - Ensure port 8081 is available"
echo "   - Check firewall settings"
echo "   - Verify container can reach external services"

echo ""
print_status "Next steps:"
echo "1. Fix any errors shown above"
echo "2. Run: $COMPOSE_CMD up --build memory-api"
echo "3. If successful, run: ./deploy_neurochat.sh"