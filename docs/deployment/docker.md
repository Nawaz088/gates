# Docker Deployment

## Production Dockerfile

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install uv && uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "gates.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose (Production)

```yaml
version: "3.8"
services:
  gates:
    build: .
    ports: ["8000:8000"]
    environment:
      - GATES_ENV=production
      - GATES_PUBLIC_URL=https://auth.yourdomain.com
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/gates
      - REDIS_URL=redis://redis:6379/0
      - GATES_FIELD_ENCRYPTION_KEY=${GATES_FIELD_ENCRYPTION_KEY}
      - GATES_JWT_SIGNING_KEY=${GATES_JWT_SIGNING_KEY}
      - GATES_COOKIE_SECURE=true
      - POSTMARK_TOKEN=${POSTMARK_TOKEN}
    depends_on: [db, redis]
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: gates
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: gates
    volumes: [pgdata:/var/lib/postgresql/data]
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  pgdata:
```

## Running Migrations

```bash
# Local
docker compose run --rm gates uv run alembic upgrade head

# In CI/CD
uv run alembic upgrade head
```

## Health Check

```bash
curl https://auth.yourdomain.com/health
# {"status":"ok","service":"gates"}
```
