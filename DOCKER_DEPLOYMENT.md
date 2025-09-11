# 🧠 NeuroChat Memory System - Docker Deployment

A complete containerized solution combining your Memory API with a ultra-modern Streamlit interface.

## 🚀 Quick Start

### 1. Clone & Deploy
```bash
git clone https://github.com/sumrendra/memory-api.git
cd memory-api
./deploy_neurochat.sh
```

### 2. Access Your System
- **NeuroChat UI**: http://localhost:8502 (Modern chat interface)
- **Memory API**: http://localhost:8081 (REST API)
- **API Docs**: http://localhost:8081/docs (Interactive documentation)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│               User Browser              │
│          http://localhost:8502          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          NeuroChat UI Container         │
│        (Streamlit + Modern UI)          │
│              Port: 8502                 │
└─────────────────┬───────────────────────┘
                  │ HTTP API Calls
┌─────────────────▼───────────────────────┐
│         Memory API Container            │
│       (FastAPI + Vector Database)       │
│              Port: 8081                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PostgreSQL Database             │
│        (External, your server)          │
└─────────────────────────────────────────┘
```

## 🐳 Docker Services

### memory-api
- **Image**: Built from your repository
- **Port**: 8081
- **Features**: 
  - Vector database storage
  - Embedding generation
  - Memory search & retrieval
  - Health monitoring

### neurochat-ui
- **Image**: Built with Streamlit
- **Port**: 8502
- **Features**:
  - Ultra-modern glass morphism UI
  - Real-time chat interface
  - Memory visualization
  - Analytics dashboard
  - Multi-device support

## ⚙️ Configuration

### Environment Variables

Copy `.env.template` to `.env` and customize:

```bash
cp .env.template .env
nano .env
```

Key settings:
```env
# Database
DATABASE_URL=postgresql://admin:password@192.168.1.4:5432/appdb

# LM Studio
LM_STUDIO_API=http://192.168.1.14:1234/v1/chat/completions

# Embedding Provider  
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

### Docker Compose Override

For custom configurations, create `docker-compose.override.yml`:

```yaml
version: "3.8"
services:
  memory-api:
    environment:
      - VECTOR_DIM=1536  # Custom dimension
      - LOG_LEVEL=DEBUG
      
  neurochat-ui:
    environment:
      - STREAMLIT_THEME=light
    ports:
      - "9000:8502"  # Custom port
```

## 🛠️ Management Commands

### Basic Operations
```bash
# Deploy/Update system
./deploy_neurochat.sh

# View logs
docker-compose logs -f

# View specific service logs  
docker-compose logs -f neurochat-ui
docker-compose logs -f memory-api

# Restart services
docker-compose restart

# Stop system
docker-compose down

# Stop and remove everything
docker-compose down -v --rmi all
```

### Development
```bash
# Rebuild containers
docker-compose up --build

# Scale UI instances
docker-compose up --scale neurochat-ui=2

# Access container shell
docker-compose exec memory-api bash
docker-compose exec neurochat-ui bash
```

## 🔍 Health Monitoring

Both services include health checks:

### Memory API
```bash
curl http://localhost:8081/health
```

### NeuroChat UI
```bash  
curl http://localhost:8502/_stcore/health
```

### Container Status
```bash
docker-compose ps
```

## 🌐 Network Access

### Local Access
- NeuroChat UI: http://localhost:8502
- Memory API: http://localhost:8081

### Network Access (from other devices)
- NeuroChat UI: http://YOUR_SERVER_IP:8502
- Memory API: http://YOUR_SERVER_IP:8081

### Portainer Integration
If using Portainer, the services will be available in your stack dashboard with full management capabilities.

## 🔧 Troubleshooting

### Common Issues

#### 1. Memory API Won't Start
```bash
# Check logs
docker-compose logs memory-api

# Common fixes:
# - Verify database connection in .env
# - Check if PostgreSQL is accessible
# - Ensure port 8081 is available
```

#### 2. UI Can't Connect to API
```bash  
# Check network connectivity
docker-compose exec neurochat-ui curl http://memory-api:8081/health

# Verify environment variables
docker-compose exec neurochat-ui printenv MEMORY_API_BASE
```

#### 3. LM Studio Connection Issues
```bash
# Test from UI container
docker-compose exec neurochat-ui curl http://192.168.1.14:1234/v1/models

# Common fixes:
# - Ensure LM Studio API is enabled
# - Check firewall settings
# - Verify IP address in configuration
```

#### 4. Database Connection Problems
```bash
# Test database connection
docker-compose exec memory-api python -c "
import psycopg2
conn = psycopg2.connect('postgresql://admin:password@192.168.1.4:5432/appdb')
print('Database connected successfully!')
"
```

### Reset Everything
```bash
# Nuclear option - reset everything
docker-compose down -v
docker system prune -a -f
./deploy_neurochat.sh
```

## 📊 Features Overview

### ✨ NeuroChat UI Features
- 🎨 **Modern Glass Morphism Design**
- 🧠 **Smart Memory Integration**
- 📱 **Mobile Responsive**
- ⚡ **Real-time Chat**
- 📊 **Memory Analytics**
- 🎛️ **AI Personality Modes**
- 🔍 **Advanced Memory Search**
- 💾 **Session Export/Import**
- 🌐 **Multi-device Sync**

### 🚀 Memory API Features
- 🧠 **Vector Database Storage**
- 🔍 **Semantic Search**
- 📝 **Automatic Chunking**
- 🎯 **Smart Deduplication**
- 📊 **Usage Analytics**
- 🔒 **Security Features**
- ⚡ **High Performance**
- 🔧 **Easy Configuration**

## 🔄 Updates & Maintenance

### Automatic Updates
The deployment script pulls latest changes:
```bash
./deploy_neurochat.sh
```

### Manual Updates
```bash
git pull origin main
docker-compose up --build -d
```

### Backup & Restore
```bash
# Backup configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup

# Export chat sessions (from UI)
# Use the "📊 Export Chat" button in the interface
```

## 🎯 Production Deployment

For production deployment on your Ubuntu server:

1. **Clone to server**:
   ```bash
   git clone https://github.com/sumrendra/memory-api.git
   cd memory-api
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   nano .env  # Update with production values
   ```

3. **Deploy with Portainer**:
   - Upload docker-compose.yml to Portainer
   - Set environment variables
   - Deploy stack

4. **Configure reverse proxy** (optional):
   - Use Nginx/Apache to serve on standard ports
   - Add SSL certificates
   - Set up domain names

## 🏆 Success! 

Your NeuroChat Memory System is now running with:
- ✅ Containerized deployment
- ✅ Ultra-modern web interface  
- ✅ Persistent memory storage
- ✅ Real-time AI chat
- ✅ Analytics & insights
- ✅ Mobile-friendly design
- ✅ Production-ready architecture

Enjoy your new AI memory system! 🎉