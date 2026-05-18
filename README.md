# MKGE — Medical Knowledge Graph Extraction + GraphRAG

## Quick Start

```bash
# 1. Copy env
cp .env.example .env
# Dien cac gia tri DB cloud vao .env

# 2. Chay backend
cd backend && pip install -e ".[dev]"
uvicorn src.mkge.main:app --reload

# 3. Migrate DB
alembic upgrade head

# 4. Chay frontend (terminal khac)
cd frontend && npm install && npm run dev
```

## Chạy bằng Docker (Khuyên dùng cho Backend)

```bash
# 1. Tạo file .env và điền các thông số cần thiết (DB, Redis...)
cp .env.example .env

# 2. Chạy toàn bộ Backend (API, Worker, Nginx, Redis) bằng Docker
docker-compose up --build -d
```

## Endpoints

- API docs: http://localhost:8000/api/docs
- Frontend: http://localhost:5173
- Health: http://localhost:8000/health

## Phase hien tai: Phase 1 (Upload + Document Management) - DONE

- [x] Auth: register / login / refresh / logout
- [x] JWT + refresh token rotation
- [x] PostgreSQL schema + Alembic migration
- [x] Frontend: Login / Register pages
- [x] Phase 1: Upload PDF + Document management (Celery worker, Local storage)
- [ ] Phase 2: Real extraction pipeline (Gemini + Llama)
- [ ] Phase 3: GraphRAG query

## DB Cloud can tao

| Service | Link |
|---|---|
| PostgreSQL | https://supabase.com |
| Neo4j | https://neo4j.com/cloud/aura-free |
| Qdrant | https://cloud.qdrant.io |
| Redis | https://upstash.com |
