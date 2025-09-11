# 🐳 Portainer Deployment Guide for NeuroChat

## 🚀 Quick Portainer Deployment

### Step 1: Upload Docker Compose File
1. **Log into Portainer**
2. **Go to Stacks** → **Add Stack**
3. **Name**: `neurochat-memory-system`
4. **Copy and paste** the contents below:

```yaml
version: "3.8"

services:
  memory-api:
    build:
      context: https://github.com/sumrendra/memory-api.git
    container_name: memory-api
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=postgresql://admin:epaps0991g@192.168.1.4:5432/appdb
      - EMBEDDING_PROVIDER=huggingface
      - VECTOR_DIM=768
      - PYTHONUNBUFFERED=1
      - UVICORN_TIMEOUT_KEEP_ALIVE=120
      - UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=30
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081", "--timeout-keep-alive", "120"]
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8081/health || exit 1"]
      interval: 60s
      timeout: 30s
      retries: 5
      start_period: 180s
    networks:
      - neurochat-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  neurochat-ui:
    build:
      context: https://github.com/sumrendra/memory-api.git
      dockerfile: Dockerfile.streamlit
    container_name: neurochat-ui
    restart: unless-stopped
    ports:
      - "8502:8502"
    environment:
      - MEMORY_API_BASE=http://memory-api:8081
      - LM_STUDIO_API=http://192.168.1.14:1234/v1/chat/completions
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ENABLE_CORS=false
    depends_on:
      - memory-api
    networks:
      - neurochat-network
    command: ["sh", "-c", "sleep 30 && streamlit run streamlit_chat.py --server.port=8502 --server.address=0.0.0.0 --browser.gatherUsageStats=false --server.headless=true"]

networks:
  neurochat-network:
    driver: bridge
```

### Step 2: Deploy Stack
1. **Click "Deploy the stack"**
2. **Wait for build** (first time may take 5-10 minutes)
3. **Monitor logs** in Portainer

## 🔧 Troubleshooting Timeout Issues

### Issue: "Read timed out" errors
**Solution**: The updated configuration includes:

✅ **Increased API timeouts** (10s → 60s)  
✅ **LLM timeout extended** (30s → 120s)  
✅ **Memory API startup time** (30s → 180s)  
✅ **Retry logic** for failed operations  
✅ **Better error handling** for container networking  

### Common Portainer Issues:

#### 1. Memory API Takes Long to Start
- **First startup** downloads embedding models (~500MB)
- **Allow 3-5 minutes** for initial deployment
- **Check logs** in Portainer → Containers → memory-api → Logs

#### 2. Container Networking Issues
- **Use container name**: `http://memory-api:8081` (not localhost)
- **Check network**: Containers should be on `neurochat-network`
- **Verify ports**: 8081 (API) and 8502 (UI) should be mapped

#### 3. Database Connection Problems
```bash
# Test from Portainer console:
docker exec -it memory-api curl http://localhost:8081/health
```

## 🌐 Access Your System

Once deployed successfully:

- **NeuroChat UI**: `http://192.168.1.4:8502`
- **Memory API**: `http://192.168.1.4:8081`
- **Health Check**: `http://192.168.1.4:8081/health`

## 🔍 Monitoring in Portainer

### Container Health
- **Green dot** = Healthy
- **Red dot** = Unhealthy
- **Yellow dot** = Starting

### Logs to Check
1. **memory-api logs**:
   - Should show "Application startup complete"
   - No database connection errors
   - Embedding model loading progress

2. **neurochat-ui logs**:
   - Should show "You can now view your Streamlit app"
   - No connection errors to memory-api

### Resource Usage
- **Memory API**: ~1-2GB RAM (embedding models)
- **NeuroChat UI**: ~200-500MB RAM
- **CPU**: Low usage when idle

## 🔄 Updates & Management

### Update Stack
1. **Portainer** → **Stacks** → **neurochat-memory-system**
2. **Click "Update the stack"**
3. **Pull and redeploy** option enabled

### Restart Services
- **Individual**: Portainer → Containers → Restart
- **Full stack**: Portainer → Stacks → Stop/Start

### Scale UI (if needed)
Add to docker-compose under neurochat-ui:
```yaml
deploy:
  replicas: 2
```

## ⚡ Performance Optimization

### For Production:
1. **Use external PostgreSQL** (not in container)
2. **Mount volumes** for persistent data
3. **Use nginx proxy** for SSL/domain
4. **Enable resource limits** as shown above

### Memory Optimization:
```yaml
environment:
  - CHUNK_SIZE=400  # Smaller chunks
  - DEDUPE_ENABLED=1  # Remove duplicates
  - VECTOR_DIM=384   # Smaller embeddings if possible
```

## 🎯 Success Indicators

Your deployment is working when:

✅ **Both containers** show green (healthy) status  
✅ **Memory API health** returns `{"status": "ok"}`  
✅ **UI loads** without connection errors  
✅ **Memory operations** work without timeouts  
✅ **Chat responses** include memory functionality  

## 🆘 Emergency Fixes

### If UI shows timeout errors:
1. **Restart memory-api** container
2. **Check database connectivity**
3. **Increase container memory** limits
4. **Wait longer** for embedding model loading

### If containers won't start:
1. **Check Portainer logs** for build errors
2. **Verify GitHub repository** is accessible
3. **Check available system resources**
4. **Try deploying services individually**

Your NeuroChat system should now work properly in Portainer with robust timeout handling! 🎉