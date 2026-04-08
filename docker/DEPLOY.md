# Jarvis (Onyx) — Deploy Guide

## Architecture

```
Internet -> Cloudflare -> Server (Docker Swarm)
                            |
                          Traefik (fabiorede)
                            |
                    jarvis.fabioviana.app.br
                            |
                          Nginx (reverse proxy)
                         /     \
                  api_server   web_server
                  (port 8080)  (port 3000)
                       |
              +--------+--------+
              |        |        |
          postgres   vespa   opensearch
          redis      minio   model_servers
```

## Services (12 containers)

| Service | Image | Memory | Purpose |
|---------|-------|--------|---------|
| api_server | onyxdotapp/onyx-backend | 4GB | FastAPI backend + Alembic migrations |
| background | onyxdotapp/onyx-backend | 4GB | Celery workers, indexing, connectors |
| web_server | onyxdotapp/onyx-web-server | 1GB | Next.js frontend |
| nginx | byfabioviana/jarvis-nginx | 256MB | Reverse proxy (Traefik-exposed) |
| inference_model_server | onyxdotapp/onyx-model-server | 3GB | Embedding/inference models |
| indexing_model_server | onyxdotapp/onyx-model-server | 3GB | Indexing-only models |
| relational_db | postgres:15.2-alpine | 256MB+ | PostgreSQL database |
| index | vespaengine/vespa:8.609.39 | 4GB | Vespa search engine |
| opensearch | opensearchproject/opensearch:3.4.0 | 4GB | Vector search |
| cache | redis:7.4-alpine | - | Redis cache |
| minio | minio/minio | - | S3-compatible file storage |
| code-interpreter | onyxdotapp/code-interpreter | 1GB | Sandbox code execution |

**Total estimated memory: ~24-28 GB**

## Prerequisites

1. Docker Swarm initialized on the server
2. Traefik running with overlay network `fabiorede`
3. DNS: `jarvis.fabioviana.app.br` -> server IP (Cloudflare, DNS only)

## GitHub Secrets Required

Configure in GitHub repo Settings > Secrets > Actions:

| Secret | Description | Example |
|--------|-------------|---------|
| `REGISTRY_USERNAME` | Docker Hub username | `byfabioviana` |
| `REGISTRY_PASSWORD` | Docker Hub password/token | |
| `PORTAINER_URL` | Portainer dashboard URL | `https://portainer.fabioviana.app.br` |
| `PORTAINER_USERNAME` | Portainer admin username | |
| `PORTAINER_PASSWORD` | Portainer admin password | |
| `PORTAINER_STACK_ID` | Stack ID (create stack first, note the ID) | `6` |
| `PORTAINER_ENDPOINT_ID` | Swarm endpoint ID | `1` |

## Portainer Stack Environment Variables

Configure in Portainer > Stacks > jarvis > Environment variables:

### Required

| Variable | Description | Generate |
|----------|-------------|----------|
| `DOMAIN` | `jarvis.fabioviana.app.br` | - |
| `POSTGRES_PASSWORD` | PostgreSQL password | `openssl rand -hex 16` |
| `USER_AUTH_SECRET` | JWT signing key | `openssl rand -hex 32` |
| `ENCRYPTION_KEY_SECRET` | Encryption key | `openssl rand -hex 32` |
| `OPENROUTER_API_KEY` | OpenRouter API key | Get from https://openrouter.ai/keys |

### Optional (have defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_TAG` | `latest` | Onyx version tag |
| `REGISTRY` | `byfabioviana` | Docker registry prefix for nginx image |
| `AUTH_TYPE` | `basic` | Auth type (basic/google_oauth/oidc/saml) |
| `POSTGRES_USER` | `postgres` | Database user |
| `S3_AWS_ACCESS_KEY_ID` | `minioadmin` | MinIO access key |
| `S3_AWS_SECRET_ACCESS_KEY` | `minioadmin` | MinIO secret key |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO root user |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO root password |
| `OPENSEARCH_ADMIN_PASSWORD` | `StrongPassword123!` | OpenSearch admin password |
| `LOG_LEVEL` | `info` | Log level |
| `ENABLE_CRAFT` | `false` | Enable AI web app builder |

## Initial Setup

### 1. Build and push nginx image

```bash
cd docker/nginx
docker build -t byfabioviana/jarvis-nginx:latest .
docker push byfabioviana/jarvis-nginx:latest
```

### 2. Create stack in Portainer

1. Go to https://portainer.fabioviana.app.br
2. Stacks > Add stack
3. Name: `jarvis`
4. Web editor: paste contents of `docker/docker-stack.yml`
5. Environment variables: add all required variables
6. Deploy the stack
7. Note the Stack ID for GitHub secrets

### 3. Configure DNS

Add A record in Cloudflare:
- Name: `jarvis`
- Content: server IP
- Proxy: DNS only (gray cloud) — Traefik handles TLS

### 4. Configure OpenRouter

After first login at https://jarvis.fabioviana.app.br:
1. Go to Admin > LLM Providers
2. Add provider: **OpenRouter**
3. API Key: (already set via env var, or enter manually)
4. Select models (e.g., `anthropic/claude-sonnet-4`, `openai/gpt-4o`)

## CI/CD Pipeline

The workflow `.github/workflows/deploy-jarvis.yml` runs on:
- Push to `main` branch (changes in `docker/` or workflow file)
- Manual trigger via GitHub Actions UI

### Manual triggers

| Target | What it does |
|--------|-------------|
| `all` | Build nginx + redeploy stack |
| `nginx-only` | Only rebuild nginx image |
| `stack-only` | Only update stack config in Portainer |
| `update-images` | Redeploy stack (pulls latest official images) |

## Updating Onyx Version

To update to a new Onyx version:
1. Change `IMAGE_TAG` in Portainer environment variables
2. Trigger manual deploy with target `update-images`

Or set `IMAGE_TAG=latest` and redeploy — it will pull the latest nightly.
