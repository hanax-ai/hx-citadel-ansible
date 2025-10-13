# Shield AG-UI Backend

FastAPI backend application for Shield AG-UI with AG-UI Python SDK integration.

## Features

- **AG-UI Protocol**: Full compliance with AG-UI protocol for LLM tool execution
- **Redis Streams Consumer**: Real-time event consumption from HX-Citadel Orchestrator
- **Server-Sent Events (SSE)**: Real-time event streaming to frontend clients
- **Authentication & RBAC**: JWT-based auth with role-based access control
- **Structured Logging**: JSON-formatted logs with structlog
- **Health Checks**: Built-in health monitoring endpoints

## Architecture

```
Backend Components:
├── FastAPI Application (main.py)
├── Redis Streams Consumer (services/redis_consumer.py)
├── Event Transformation Service (services/event_service.py)
├── SSE Endpoint (/events)
└── API Endpoints (/api/*, /auth/*, /admin/*)
```

## Environment Variables

Required environment variables:

```bash
# External Services
LITELLM_URL=http://hx-litellm-server:4000
ORCHESTRATOR_URL=http://hx-orchestrator-server:8000
REDIS_URL=redis://hx-sqldb-server:6379
QDRANT_URL=http://hx-vectordb-server:6333
DATABASE_URL=postgresql://shield:shield@hx-sqldb-server:5432/shield

# Redis Streams
REDIS_STREAM_NAME=shield:events
REDIS_CONSUMER_GROUP=ag-ui-clients
REDIS_CONSUMER_NAME=hx-dev-server

# Authentication
JWT_SECRET=your-secret-key
LITELLM_API_KEY=sk-shield-lob-default

# CORS
CORS_ORIGINS=http://localhost:3001,http://localhost:80
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --reload --port 8002

# Run tests
pytest tests/ -v
```

## Docker

```bash
# Build image
docker build -t shield-ag-ui-backend:latest .

# Run container
docker run -p 8002:8002 \
  -e REDIS_URL=redis://host:6379 \
  -e LITELLM_URL=http://host:4000 \
  shield-ag-ui-backend:latest
```

## API Documentation

- Interactive API docs: http://localhost:8002/docs
- OpenAPI schema: http://localhost:8002/openapi.json
- Health check: http://localhost:8002/health

## Event Flow

1. Orchestrator publishes events to Redis Streams (`shield:events`)
2. Backend Redis consumer reads events using XREADGROUP
3. Events transformed to AG-UI protocol format
4. Events streamed to frontend via SSE endpoint `/events`
5. Frontend receives real-time updates for job progress, tool execution, etc.

## Security

- Non-root user in Docker container
- JWT-based authentication
- RBAC with 3 roles (Admin, Contributor, Viewer)
- CORS protection
- No secrets in version control

## License

Proprietary - HX-Citadel Shield Team
