# PROJECT_CONTEXT.md
# Medical Knowledge Graph Extraction (MKGE) + GraphRAG
# Được tổng hợp từ session thiết kế kiến trúc — dùng để onboard chat mới

---

## 0. Đọc file này như thế nào

Đây là **single source of truth** cho toàn bộ dự án BTL. Mọi quyết định kỹ thuật,
lý do chọn/bỏ công nghệ, roadmap, deployment đều có ở đây. Khi hỏi AI trong chat
mới, paste file này vào đầu conversation.

---

## 1. Tổng quan dự án

| Thuộc tính | Chi tiết |
|---|---|
| Tên | Hệ thống Trích xuất Đồ thị Tri thức Y khoa (MKGE) |
| Loại | Web-based Platform |
| Scope | BTL cuối kỳ — team 3-4 người, 6 tuần |
| Môn học | Vấn đề Khoa học Máy tính |

### Mục tiêu cốt lõi

1. Upload PDF y khoa (báo cáo nghiên cứu, hồ sơ bệnh án đã ẩn danh)
2. Tự động trích xuất 3 loại thực thể: **Drug, Disease, Symptom** + quan hệ nhân quả/điều trị
3. Lưu vào Knowledge Graph (Neo4j) + Vector DB (Qdrant)
4. Truy vấn ngôn ngữ tự nhiên qua **GraphRAG** → trả lời kèm sub-graph + citation về trang PDF gốc

### Đóng góp khoa học (Research Gap giải quyết)

| Gap | Giải pháp của dự án |
|---|---|
| OCR phá vỡ bảng biểu PDF | Gemini 3 Flash multimodal đọc thẳng PDF |
| Hallucination LLM ghi thẳng vào DB | Dual-Model: Gemini extract → Llama verify |
| RAG không có multi-hop reasoning | GraphRAG: vector search → graph traversal |

---

## 2. Kiến trúc hệ thống

### Kiến trúc tổng thể: Modular Monolith + Clean Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                             │
│        React 18 + Vite + TS / Cytoscape.js / TanStack Query    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────────┐
│                  NGINX (Reverse Proxy)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│          FastAPI Application (Modular Monolith)                 │
│  ┌────────┬──────────┬─────────┬──────────┬──────────────────┐  │
│  │  auth  │documents │  graph  │  query   │     admin        │  │
│  └────────┴──────────┴─────────┴──────────┴──────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         Application Layer (Use Cases / Services)        │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │   Infrastructure: LLM Gateway · Repos · Storage         │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────┬──────────┬────────┬──────────┬──────────┬────────────────┘
       │          │        │          │          │
    Redis      Postgres  Neo4j     Qdrant    LLM APIs
    Broker+    metadata  KG        Vectors   Gemini/Groq
    Cache
       │
┌──────▼──────────────────────────┐
│   Celery Workers (concurrency=1) │
│   parse_pdf → extract → verify   │
│   → persist_graph + embeddings   │
└─────────────────────────────────┘
```

### Tại sao Modular Monolith (không phải Microservices)

- Team 3-4 người → Microservices overkill, tốn 2-3 tuần setup
- Scope BTL: 5-10 concurrent users → không cần scale per-service
- Vẫn giữ ranh giới module nghiêm ngặt → dễ tách microservices sau

---

## 3. Module Breakdown

| Module | Trách nhiệm | MVP? |
|---|---|---|
| `auth` | Register, login, JWT, refresh token, bcrypt | ✅ BẮT BUỘC |
| `users` | Profile, role management | ✅ BẮT BUỘC |
| `documents` | Upload PDF, metadata, list/search/delete | ✅ BẮT BUỘC |
| `pipeline` | Orchestrate Celery: parse→extract→verify→persist | ✅ BẮT BUỘC |
| `llm_gateway` | Wrapper Gemini/Groq, retry, fallback, rate-limit | ✅ BẮT BUỘC |
| `graph` | Đọc Neo4j, build sub-graph, export | ✅ BẮT BUỘC |
| `query` | GraphRAG: embed + vector search + cypher + LLM | ✅ BẮT BUỘC |
| `notifications` | Polling endpoint `/documents/{id}` status | ✅ BẮT BUỘC |
| `admin` | User list, system stats, audit log view | 🟡 Nice-to-have |
| `audit` | Log upload/query vào Postgres | 🟡 Nice-to-have |
| `export` | Export graph JSON/PNG | 🟡 Nice-to-have |

### Quy tắc gọi giữa module (BẮT BUỘC tuân theo)

- Module gọi nhau **chỉ qua service layer**, không import repo của module khác
- Cross-module event → qua Redis pub/sub
- `domain` không import gì ngoài stdlib + Pydantic
- `infrastructure` implement interface ở `application`

---

## 4. Database Design

### 4.1 PostgreSQL (metadata)

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin','researcher','viewer')),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename       TEXT NOT NULL,
    file_path      TEXT NOT NULL,
    file_size      BIGINT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','parsing','extracting',
                                     'verifying','done','failed')),
    error_message  TEXT,
    entity_count   INT DEFAULT 0,
    relation_count INT DEFAULT 0,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    processed_at   TIMESTAMPTZ
);
CREATE INDEX idx_documents_user_status ON documents(user_id, status);

CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE query_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    question    TEXT NOT NULL,
    answer      TEXT,
    latency_ms  INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Neo4j (Knowledge Graph)

**Node labels:**
```
(:Drug    {id, name, normalized_name, source_doc_ids: [uuid]})
(:Disease {id, name, normalized_name, icd10?, source_doc_ids: [uuid]})
(:Symptom {id, name, normalized_name, source_doc_ids: [uuid]})
(:Document {id, filename, user_id})
(:Chunk   {id, doc_id, page, text, qdrant_id})
```

**Relationship types:**
```
(:Drug)-[:TREATS          {confidence, source_chunk_ids, verified_by}]->(:Disease)
(:Drug)-[:CAUSES_SE       {confidence}]->(:Symptom)
(:Disease)-[:HAS_SYMPTOM  {confidence, source_chunk_ids}]->(:Symptom)
(:Disease)-[:COMORBID     {confidence}]->(:Disease)
(:Document)-[:CONTAINS]->(:Chunk)
(:Chunk)-[:MENTIONS]->(:Drug|:Disease|:Symptom)
```

**Constraints (BẮT BUỘC tạo trước khi ingest data):**
```cypher
CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (s:Symptom) REQUIRE s.id IS UNIQUE;
CREATE INDEX drug_norm IF NOT EXISTS FOR (d:Drug) ON (d.normalized_name);
CREATE FULLTEXT INDEX entity_search FOR (n:Drug|Disease|Symptom) ON EACH [n.name];
```

**Cypher query mẫu (GraphRAG multi-hop):**
```cypher
MATCH (s:Symptom)<-[:HAS_SYMPTOM]-(d:Disease)<-[:TREATS]-(drug:Drug)
WHERE s.id IN $symptom_ids
WITH drug, d, collect(DISTINCT s.name) AS via_symptoms
OPTIONAL MATCH (drug)-[:CAUSES_SE]->(se:Symptom)
RETURN drug.name, d.name, via_symptoms,
       collect(DISTINCT se.name) AS side_effects,
       drug.source_doc_ids AS sources
LIMIT 20;
```

### 4.3 Qdrant (Vector DB) — dùng Qdrant thay Milvus

> **Lý do chọn Qdrant:** Dễ deploy hơn Milvus, REST API tốt hơn, payload filter mạnh. Milvus overkill cho BTL.

```python
collection_config = {
    "name": "medical_chunks",
    "vectors": {"size": 768, "distance": "Cosine"},  # Gemini text-embedding-004
    "payload": {
        "chunk_id":   "keyword",
        "doc_id":     "keyword",
        "user_id":    "keyword",
        "page":       "integer",
        "text":       "text",
        "entity_ids": "keyword[]"
    }
}
```

**QUAN TRỌNG:** Embedding model phải nhất quán ingestion <-> query:
```python
EMBEDDING_MODEL = "models/gemini-embedding-001"  # Gemini API (text-embedding-004 đã deprecated)
EMBEDDING_DIMS  = 768  # gemini-embedding-001 mặc định 3072, ta truyền output_dimensionality=768 để giữ contract
```

### 4.4 Redis (Cache + Broker)

```
# Cache
cache:query:{sha256(question)}          -> JSON response   TTL 1h
cache:embed:{sha256(text)}              -> vector bytes    TTL 24h

# Auth
auth:rate_limit:{user_id}:{endpoint}    -> counter         TTL 60s

# Celery (managed tự động)
celery-task-meta-*
```

---

## 5. Authentication & Authorization

### JWT Flow
- **Access token:** HS256, claims `{sub, role, exp, iat}`, TTL **15 phút**
- **Refresh token:** random 256-bit, hash SHA-256 lưu DB, TTL **7 ngày**, rotate mỗi lần dùng

### Role -> Permission

| Permission | admin | researcher | viewer |
|---|---|---|---|
| Upload PDF | YES | YES | NO |
| View own docs | YES | YES | NO |
| View all docs | YES | NO | NO |
| Query GraphRAG | YES | YES | YES |
| View public KG | YES | YES | YES |
| Delete user | YES | NO | NO |

### FastAPI Dependency pattern

```python
# interface/api/deps.py
def require_role(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Forbidden")
        return user
    return checker

# Usage
@router.post("/documents", dependencies=[Depends(require_role("admin","researcher"))])
async def upload_doc(...): ...
```

---

## 6. API Design

### Endpoint Catalog `/api/v1`

| Method | Path | Auth | Mo ta |
|---|---|---|---|
| POST | `/auth/register` | No | Dang ky |
| POST | `/auth/login` | No | Login -> tokens |
| POST | `/auth/refresh` | No | Rotate refresh token |
| POST | `/auth/logout` | Yes | Revoke refresh |
| GET | `/users/me` | Yes | Profile |
| POST | `/documents` | Yes researcher+ | Upload PDF |
| GET | `/documents` | Yes | List (paginated) |
| GET | `/documents/{id}` | Yes | Detail + status (dung cho polling) |
| DELETE | `/documents/{id}` | Yes | Xoa |
| GET | `/graph/overview` | Yes | Toan bo KG |
| GET | `/graph/entity/{id}` | Yes | Sub-graph quanh entity |
| POST | `/query` | Yes | GraphRAG question |
| GET | `/query/history` | Yes | Lich su query |
| GET | `/admin/users` | Yes admin | List users |
| GET | `/health` | No | Liveness check |

### Error Format chuan

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document 8f3a... does not exist",
    "details": {"document_id": "8f3a..."},
    "request_id": "req_a1b2c3d4"
  }
}
```

### Progress tracking: POLLING (khong phai SSE)

> **Ly do:** Render free tier timeout HTTP sau 30 giay -> SSE bi ngat.
> Dung polling don gian hon va khong phu thuoc infrastructure.

```typescript
// Frontend poll GET /documents/{id} moi 3 giay
const useDocumentProgress = (docId: string) => {
  return useQuery({
    queryKey: ['doc-progress', docId],
    queryFn: () => api.get(`/documents/${docId}`),
    refetchInterval: (data) =>
      ['done', 'failed'].includes(data?.status) ? false : 3000,
  })
}
```

---

## 7. Folder Structure

### Backend (Clean Architecture)

```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/versions/
├── tests/
│   ├── unit/
│   └── integration/
└── src/mkge/
    ├── main.py               # FastAPI app factory
    ├── config.py             # Pydantic Settings (doc tu .env)
    ├── domain/               # PURE — chi stdlib + Pydantic
    │   ├── entities/         # User, Document, Entity, Relation
    │   ├── value_objects/    # EmailAddress, DocumentStatus
    │   └── exceptions.py
    ├── application/          # Use cases
    │   ├── auth/services.py
    │   ├── documents/services.py
    │   ├── pipeline/
    │   │   ├── parse_pdf.py
    │   │   ├── extract.py
    │   │   ├── verify.py
    │   │   └── persist.py
    │   └── query/graphrag.py
    ├── infrastructure/       # Implementation chi tiet
    │   ├── db/
    │   │   ├── postgres/     # SQLAlchemy models + repos
    │   │   ├── neo4j/        # driver + graph_repo
    │   │   └── qdrant/       # vector_repo
    │   ├── llm/
    │   │   ├── gateway.py    # Interface + fallback logic
    │   │   ├── gemini_client.py
    │   │   ├── groq_client.py
    │   │   └── prompts/      # Jinja2 templates
    │   ├── cache/            # Redis wrapper
    │   ├── storage/          # File storage abstraction
    │   └── celery_app.py
    ├── interface/
    │   ├── api/v1/           # Routes: auth, documents, graph, query, admin
    │   ├── api/deps.py       # FastAPI Dependencies
    │   ├── api/middleware.py # logging, request_id, CORS
    │   ├── api/errors.py     # Exception handlers
    │   └── workers/tasks.py  # Celery task definitions
    └── shared/
        ├── logging.py        # structlog config
        ├── security.py       # hash, jwt
        └── utils.py
```

### Frontend (Feature-based)

```
frontend/
└── src/
    ├── features/
    │   ├── auth/             # api.ts, hooks.ts, components/, store.ts
    │   ├── documents/        # UploadZone, DocumentList, ProgressTracker
    │   ├── graph/            # GraphViewer (Cytoscape), NodeDetail, FilterPanel
    │   └── query/            # ChatBox, AnswerCard, CitationList
    ├── shared/
    │   ├── components/       # Button, Modal, Toast
    │   ├── lib/              # axios instance, query client
    │   ├── hooks/            # useDebounce, usePolling
    │   └── types/            # shared TS types
    ├── pages/                # Route components (mong, chi compose features)
    └── styles/globals.css
```

---

## 8. Tech Stack Day du

| Layer | Cong nghe | Ghi chu |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | |
| UI | TailwindCSS + shadcn/ui | |
| Graph render | Cytoscape.js | |
| State | Zustand + TanStack Query | |
| Backend | Python 3.11+, FastAPI | |
| Validation | Pydantic v2 | |
| ORM | SQLAlchemy 2.0 + Alembic | |
| Task queue | Celery + Redis | concurrency=1 tren free tier |
| Graph DB | Neo4j 5 (Aura Free) | 50k nodes, du BTL |
| Vector DB | Qdrant Cloud Free | 1GB cluster |
| Relational DB | PostgreSQL (Supabase free) | 500MB |
| Cache/Broker | Redis (Upstash free) | 10k cmd/day |
| AI Parse | Gemini 2.5 Flash | multimodal PDF → Markdown (Gemini 3 chưa public, swap khi ra) |
| AI Extract NER | Gemini 2.5 Flash | text NER, primary path |
| AI NER fallback | Groq Llama 4 Scout | khi Gemini 429 quota cạn (free tier 20 RPD) |
| AI Verify | Llama 4 Scout via Groq Cloud | cross-check rels, threshold conf ≥ 0.7 |
| Embedding | Gemini `gemini-embedding-001` (output_dim=768) | text-embedding-004 deprecated |
| File storage | Local disk (MVP) | |
| Proxy | Nginx | |
| Container | Docker + Docker Compose | |
| Frontend deploy | Vercel (free) | |
| Backend deploy | Render (free tier) | sleep sau 15 phut |
| Keep-alive | UptimeRobot ping /health moi 5 phut | |

---

## 9. Hai Pipeline Chinh

### Pipeline 1: Ingestion (async qua Celery)

```
PDF Upload -> FastAPI (202 + doc_id) -> Celery task enqueued
  Worker:
    1. parse_pdf:           Gemini multimodal -> Markdown (bao toan bang bieu)
                            Fallback: pdfplumber raw text + "## Trang N" headings
                            Đồng thời pdfplumber tách (page_num, text) cho chunks
    2a. structural_parse:   Parse Markdown -> heading tree (Section{level, title, body})
                            Skip noise sections: References/Mục lục/Phụ lục/Acknowledg
                            (language-agnostic VN+EN)
    2b. extract_entities:   Per-section NER. Mỗi section qua Gemini (primary) hoặc
                            Groq Llama (fallback 429). Prompt blacklist: bỏ
                            xét nghiệm/thủ thuật/lab values/references/đơn vị đo.
    2c. structural_infer:   Hướng 3 ontology-based. Detect "topic" của section qua regex:
                              - "(điều\s*trị|phác\s*đồ|chữa)\s+(.+)"      -> TREATS topic_disease
                              - "(triệu\s*chứng|biểu\s*hiện)\s+(.+)"      -> HAS_SYMPTOM topic_disease -> ent
                              - "(tác\s*dụng\s*phụ)\s+(.+)?"              -> CAUSES_SE topic_drug -> ent
                            Với mỗi entity trong section match topic + đúng EntityType,
                            sinh relationship với confidence=0.75 và evidence là heading_path
    3. verify_relations:    Llama 4/Groq cross-check từng rel (batch 8) -> {verified, confidence, reason}
                            DROP nếu verified=false hoặc confidence < 0.7
    3b. assign_chunks:      Map mỗi rel với chunk PDF chứa cả source.name + target.name
                            (so sánh sau khi strip diacritics tiếng Việt)
                            DROP rel nào không tìm được chunk evidence
    4. generate_embeddings: Gemini gemini-embedding-001 (output_dim=768) cho mỗi chunk
                            Fallback: zero vector + log warning
    5. persist_graph:       Cypher batch -> Neo4j (Drug/Disease/Symptom/Document/Chunk +
                            CONTAINS/MENTIONS/TREATS/CAUSES_SE/HAS_SYMPTOM/COMORBID)
                            + Qdrant upsert (chunk_id, user_id, page, text, entity_ids)
    6. update_status:       Postgres documents.status = 'done' + entity_count + relation_count
```

**Anti-hallucination rule:** Mọi edge y khoa Neo4j **BẮT BUỘC** có `source_chunk_ids` non-empty
(chunk PDF chứa cả 2 entity → evidence vật lý, không phải LLM bịa).

### Pipeline 2: GraphRAG Query (sync voi cache)

```
Question -> check Redis cache (hit -> return ngay)
         -> Gemini embedding -> vector
         -> Qdrant search -> top-k entity IDs
         -> Cypher traversal -> sub-graph (depth <= 2, LIMIT 50)
         -> assemble context (text + graph)
         -> Llama 4 generate answer + validate citation chunk_ids
         -> cache response (TTL 1h)
         -> return {answer, subgraph, citations}
```

---

## 10. Cac Loi Thuong Gap (Can Tranh)

### LLM Pipeline

| Loi | Phong tranh |
|---|---|
| Hallucination leak vao DB | Verify step bat buoc, drop neu is_valid=false, moi edge can source_chunk_ids |
| Cost runaway (het quota) | Cache embedding + response, rate limit per user (5 upload/h, 30 query/h) |
| Schema drift (LLM doi format output) | Dung Gemini response_schema + Pydantic validate, retry max 2 lan |

### Kien truc

| Loi | Phong tranh |
|---|---|
| God service | Moi service <= 200 dong |
| Sync block (upload cho LLM 30s) | Endpoint chi enqueue -> 202, frontend polling |
| Hardcode secret | .env + pydantic_settings.BaseSettings |
| Logic trong route | Route chi parse + goi service |
| Cypher injection | LUON dung $param, khong format string |

---

## 11. Roadmap BTL theo Phase (6 tuan)

### PHASE 0 — Foundation (3-4 ngay)
**Demo duoc:** docker-compose up + dang ky/login hoat dong

- Setup repo + Docker Compose + .env.example
- Ket noi 4 DB cloud (Neo4j Aura + Qdrant + Supabase + Upstash)
- Auth module: register/login/refresh + JWT
- Frontend skeleton + LoginPage/RegisterPage

DoD: Clone + dien .env -> chay duoc | Register -> Login -> vao dashboard

---

### PHASE 1 — Upload + Document Management (1 tuan)
**Demo duoc:** Upload PDF -> thay trong list -> xoa duoc

- documents module: model, repo, service, endpoints
- File storage local + validate
- Celery stub task (sleep 5s -> status DONE)
- Frontend: UploadZone + DocumentList + ProgressTracker (polling)

Rui ro: Nginx client_max_body_size phai set >= 50MB

---

### PHASE 2 — Real Extraction Pipeline (1.5 tuan) [PHASE QUAN TRONG NHAT] ✅ DONE 2026-05-20
**DoD đạt được:** Upload PDF y khoa -> ~72s sau -> graph có entity thật từ file

- ✅ Pipeline thật 6 stage (parse → structural → NER → verify → embed → persist)
- ✅ Hybrid Gemini→Groq fallback (chưa abstract thành LLM Gateway riêng — TODO Phase 4)
- ✅ Neo4j repo (Drug/Disease/Symptom/Document/Chunk + 6 rel types) + Qdrant repo (768 dim)
- ✅ Frontend GraphViewer Cytoscape.js với 3 màu entity + 4 relation type
- ✅ Anti-hallucination: source_chunk_ids non-empty + strip diacritics matching
- ✅ Hướng 3 ontology inference từ heading regex

**Kết quả thực tế đo được:**
- PDF Bộ Y tế 18 trang → 142 entities, 45 relationships, 18 chunks (940s lần đầu, 72s sau cache)
- PDF viêm phế quản 4 trang → 69 entities, 24 rels, 4 chunks, 72s end-to-end

---

### PHASE 3 — GraphRAG Query (1 tuan)
**Demo duoc:** Chat hoi -> tra loi + sub-graph + click citation ve dung trang PDF

- Query use case: embed -> Qdrant -> Cypher -> context -> Llama generate
- Citation linking
- Redis cache query response
- Frontend: ChatBox + AnswerCard + CitationList

---

### PHASE 4 — Polish + Admin + Demo Prep (1 tuan)
**Demo duoc:** Demo 10 phut hoan chinh khong loi

- Rate limiting, error handling
- Admin dashboard: user list + stats
- Bug bash + unit test
- README + sequence diagram + ERD

---

### PHASE 5 — Stretch Goals (neu con thoi gian)

| Feature | Wow factor | Effort |
|---|---|---|
| Compare 2 documents (diff KG) | **** | Cao — rat an tuong |
| LLM cost dashboard | *** | Trung |
| Export graph PNG/JSON | ** | Thap |

---

## 12. Deployment Strategy

### Hien tai (khong can Oracle, chay ngay)

```
Vercel        -> Frontend React (free)
Render        -> FastAPI + Celery worker (free, sleep sau 15 phut)
UptimeRobot   -> Ping /health moi 5 phut -> Render khong ngu (free)

Neo4j Aura Free  -> Graph DB   (neo4j.com/cloud/aura-free)
Qdrant Cloud     -> Vector DB  (cloud.qdrant.io)
Supabase         -> Postgres   (supabase.com)
Upstash          -> Redis      (upstash.com)
```

**Ly do khong dung local embedding model:**
Render free chi co 512MB RAM. sentence-transformers ton ~350MB.
Thay bang Gemini embedding API -> worker chi dung ~150MB.

### Khi Oracle dang ky duoc -> migrate

```
Oracle A1 Free: 24GB RAM, 4 vCPU ARM
-> docker-compose up voi tat ca DB self-hosted
-> Chi doi connection string trong .env
-> Code khong thay doi gi
```

### .env can co

```env
# Auth
JWT_SECRET=<random 64 chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL (Supabase)
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres

# Neo4j (Aura Free)
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxxx

# Qdrant Cloud
QDRANT_URL=https://xxxx.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=xxxx

# Redis (Upstash)
REDIS_URL=rediss://default:xxxx@xxx.upstash.io:6379
CELERY_BROKER_URL=rediss://default:xxxx@xxx.upstash.io:6379

# AI APIs
GEMINI_API_KEY=xxxx
GROQ_API_KEY=xxxx

# Embedding (text-embedding-004 deprecated -> dung gemini-embedding-001 voi output_dimensionality=768)
EMBEDDING_MODEL=models/gemini-embedding-001
EMBEDDING_DIMS=768

# App
MAX_UPLOAD_SIZE_MB=50
RATE_LIMIT_UPLOAD_PER_HOUR=5
RATE_LIMIT_QUERY_PER_HOUR=30
```

---

## 13. Quyet dinh ky thuat da chot (khong can ban lai)

| Quyet dinh | Ly do |
|---|---|
| Modular Monolith, khong phai Microservices | Team nho, scope BTL |
| Qdrant thay Milvus | De deploy, free tier tot hon |
| Polling thay SSE | Render timeout 30s pha SSE |
| Gemini embedding API thay local model | Tiet kiem RAM Render |
| Dual-Model (Gemini extract + Llama verify) | Core contribution, chong hallucination |
| Confidence threshold 0.7 + source_chunk_ids bat buoc | Safety cho y khoa |
| concurrency=1 cho Celery worker | Fit free tier 512MB |
| **Hybrid Gemini→Groq fallback ở NER** (chốt Phase 2) | Gemini free tier 20 RPD cạn nhanh; fallback Groq giữ pipeline chạy. Đánh đổi: khi fallback, mất tính dual-model khách quan vì cùng Groq làm cả NER lẫn Verify |
| **Skip noise sections** (References/Mục lục/Phụ lục/Acknowledgments) | Tránh entity giả từ tên bài báo tiếng Anh trong references VN paper. Regex language-agnostic (VN \| EN) |
| **NER prompt blacklist explicit** thay vì thêm entity type | Văn bản y khoa có xét nghiệm/thủ thuật/lab values/đơn vị đo dễ bị Llama nhét sai. Plan giữ 3 type (Drug/Disease/Symptom), prompt liệt kê rõ "KHÔNG TRÍCH" để không phình schema |
| **Page-aware chunks** (1 page = 1 chunk, split nếu >4K chars) | Anti-hallucination cần `source_chunk_ids` với page number → citation về đúng trang PDF gốc (yêu cầu §11 Phase 3) |
| **Hướng 3: structural inference từ heading regex** | PDF guideline y khoa viết kiểu phân nhóm ("Các thuốc gồm: A, B, C"), không có câu "A điều trị X" tường minh. Sentence-level NER miss. Suy luận từ section heading → bù recall, verifier vẫn validate |
| **Strip diacritics khi match chunk** | normalized_name "tang huyet ap" không match chunk text "Tăng huyết áp" → phải strip dấu cả 2 bên. Lỗi này khiến 31/51 rel bị drop oan trước khi fix |

---

## 14. Trang thai hien tai (cap nhat 2026-05-25 — BẢN FINAL)

**Phase đang làm:** ✅ Tất cả 5 phase (0→4) đã DONE. Branch `final` = merge của `phase4`.

**Đã hoàn thành:**
- ✅ Phase 0 (Foundation): Auth + 4 DB cloud + Docker Compose
- ✅ Phase 1 (Upload + Document Management): UploadZone + DocumentTable + polling status
- ✅ Phase 2 (Real Extraction Pipeline): Pipeline 6 stage + Hướng 3 ontology + anti-hallucination
- ✅ Phase 3 (GraphRAG Query): embed → Qdrant → Neo4j subgraph → Gemini answer + ChatBox + history + citations + 1-hop subgraph viewer
- ✅ Phase 4 (Polish + Admin): rate limiting (sliding window Redis) + admin dashboard (users/stats/audit) + audit log + 13 unit tests + XSS fix + Settings page với RAG params động

**Còn lại (out-of-scope BTL, optional Phase 5 stretch):**
- LLM cost dashboard
- Compare 2 documents (diff KG)
- Export graph PNG/JSON
- Migrate sang Oracle A1 Free khi đăng ký được (chỉ đổi connection string trong .env, code không thay đổi)

**Oracle:** Chưa đăng ký được → không block gì, dùng managed DB cloud trước (Supabase + Neo4j Aura + Qdrant Cloud + Upstash).

---

## 15. Implementation Notes (Phase 2)

Section này gom các deviation từ plan ban đầu + lý do thực tế khi triển khai.
Tách khỏi §1-13 để giữ plan gốc sạch.

### 15.1 Deviation đã được approve

| Deviation | Plan gốc | Thực tế | Lý do |
|---|---|---|---|
| Model Gemini | "Gemini 3 Flash" | `gemini-2.5-flash` | Gemini 3 chưa public 2026-05 |
| Model embedding | `models/text-embedding-004` | `models/gemini-embedding-001` (output_dim=768) | text-embedding-004 đã deprecated. Giữ 768 dim để khớp Qdrant collection |
| Model verify | "Llama 4 via Groq" | `meta-llama/llama-4-scout-17b-16e-instruct` | Llama 4 Scout là biến thể public trên Groq |
| LLM Gateway module | Có (§3) | **Không abstract** (accepted tech debt) | Pattern Gemini-primary + Groq-fallback đã lặp 4 lần (ner/verifier/embedder/llm_generator). Refactor tiết kiệm ~50 dòng nhưng thêm 1 lớp indirection. Scope BTL không justify. Sửa khi swap model là acceptable |
| FULLTEXT INDEX entity_search | Có (§4.2) | Chưa tạo | GraphRAG Phase 3 dùng Qdrant vector search + Neo4j ID lookup, không cần FULLTEXT |

### 15.2 Bug đã fix có thể tái xuất hiện

| Bug | Trigger | Fix |
|---|---|---|
| Duplicate upload 2 POST | React StrictMode + side effect trong setState | Module-level Map dedupe 1500ms + side effect ra ngoài setState |
| Supabase pgbouncer timeout | Port 6543 transaction pooler + real pool | Đổi 5432 session pooler + pool_size=5 |
| Celery asyncio loop conflict | Shared engine từ FastAPI startup loop | Mỗi Celery task tạo NullPool engine riêng, dispose sau |
| Gemini 429 toàn pipeline | Free tier 20 RPD chung cho generateContent | Hybrid Gemini→Groq fallback ở NER. Parsing fallback pdfplumber |
| Source chunks drop nhầm 31/51 rels | normalized_name "tang huyet ap" không match chunk "Tăng huyết áp" | `_strip_diacritics` (unicodedata.NFD) cho cả chunk text trước khi `in` check |
| Embedding zero vectors | text-embedding-004 deprecated | Thử model list, dùng output_dimensionality=768 cho gemini-embedding-001 |
| Worker treo lâu ở Gemini call | SDK không có default timeout | Thêm `request_options={"timeout": N}` cho mọi Gemini call |
| Neo4j relationship type literal | Cypher MERGE cần literal type, không param hoá được | Group rels by type, batch query một câu Cypher per type |

### 15.3 Quota Gemini free tier (quan trọng)

- `gemini-2.5-flash`: 10 RPM, **20 RPD** (project mới)
- `gemini-embedding-001`: 100 RPD riêng
- 1 PDF 18 trang ≈ 1 parsing + 18 NER = 19 calls → cạn quota 1 ngày trong 1 upload
- Khi cạn: parsing fallback pdfplumber (mất Markdown thật → Hướng 3 vô hiệu), NER fallback Groq (mất quality)
- Giải pháp: enable billing GCP ($300 free credit), không cần đổi code

### 15.4 Files Phase 2 đã tạo/sửa

**Backend domain:** [graph.py](backend/src/mkge/domain/entities/graph.py), [chunk.py](backend/src/mkge/domain/entities/chunk.py)

**Backend pipeline:** [extractor.py](backend/src/mkge/application/pipeline/extractor.py), [ner.py](backend/src/mkge/application/pipeline/ner.py), [structural.py](backend/src/mkge/application/pipeline/structural.py), [verifier.py](backend/src/mkge/application/pipeline/verifier.py), [embedder.py](backend/src/mkge/application/pipeline/embedder.py), [service.py](backend/src/mkge/application/pipeline/service.py)

**Backend infrastructure:** [graph_repo.py](backend/src/mkge/infrastructure/db/neo4j/graph_repo.py), [vector_repo.py](backend/src/mkge/infrastructure/db/qdrant/vector_repo.py), [tasks.py](backend/src/mkge/interface/workers/tasks.py)

**Backend interface:** [graph.py](backend/src/mkge/interface/api/v1/graph.py)

**Frontend:** [GraphViewer.tsx](frontend/src/features/graph/GraphViewer.tsx), [GraphPage.tsx](frontend/src/pages/GraphPage.tsx), [api.ts](frontend/src/features/graph/api.ts), [hooks.ts](frontend/src/features/graph/hooks.ts), [types/index.ts](frontend/src/shared/types/index.ts)

**Scripts/test:** [wipe_neo4j.py](backend/wipe_neo4j.py), [test_gemini.py](backend/test_gemini.py), [test_gemini_pdf.py](backend/test_gemini_pdf.py), [test_medical.html](backend/test_medical.html)

---

### 15.5 Implementation Notes — Phase 3 (GraphRAG Query)

**Deviation đã được approve:**

| Deviation | Plan gốc | Thực tế | Lý do |
|---|---|---|---|
| Answer model | "Llama via Groq" | `gemini-2.5-flash` primary + Groq fallback | Gemini cho câu trả lời tiếng Việt tự nhiên hơn cho y khoa; giữ Groq fallback khi quota cạn |
| `application/query/graphrag.py` | Tên file trong plan | `application/query/service.py` | Tên ngắn hơn, đồng bộ với `auth/services.py`, `documents/services.py` |
| 1-hop subgraph viewer kèm câu trả lời | Không có trong plan | Đã thêm | UX: user thấy ngay tri thức nền của answer, kiểm chứng nhanh |
| Dynamic `top_k` + `temperature` | Hardcoded 0.2 trong plan | Cho phép user chỉnh qua Settings | Lưu localStorage, gửi xuống API mỗi query |
| Citation về trang PDF | Plan ghi "click → trang" | Hiển thị page + snippet trong CitationList | Không cần PDF viewer overlay → đỡ phức tạp |

**Bug đã fix:**

| Bug | Trigger | Fix |
|---|---|---|
| PDF extract dính chữ liền nhau | pdfplumber default mode không add space giữa text segments | `extract_words()` + join lại với space, fix word spacing |
| LLM trả "không có thông tin" nhưng vẫn render citations | UI luôn show chunks dù answer = "không tìm thấy" | Detect negative keywords trong answer → ẩn citations khi không liên quan |
| Query timeout 30s ngắt giữa chừng | Axios default 30s, Gemini đôi khi chậm | Tăng timeout client lên 60s |

**Files Phase 3 đã tạo/sửa:**
- Backend: [query/service.py](backend/src/mkge/application/query/service.py), [cache/redis.py](backend/src/mkge/infrastructure/cache/redis.py), [llm_generator.py](backend/src/mkge/infrastructure/llm/llm_generator.py), [query_history_repo.py](backend/src/mkge/infrastructure/db/postgres/query_history_repo.py), [api/v1/query.py](backend/src/mkge/interface/api/v1/query.py)
- Frontend: [QueryPage.tsx](frontend/src/pages/QueryPage.tsx), [QueryHistoryPage.tsx](frontend/src/pages/QueryHistoryPage.tsx), [features/query/](frontend/src/features/query/) (ChatBox + AnswerCard + CitationList + QueryService)

---

### 15.6 Implementation Notes — Phase 4 (Polish + Admin)

**Deviation đã được approve:**

| Deviation | Plan gốc | Thực tế | Lý do |
|---|---|---|---|
| Settings page | Không có trong plan | Đã thêm `/settings` (profile + theme + RAG params) | Cần chỗ chứa RAG params động (top_k/temperature) → tiện làm full settings luôn |
| Cascade delete user | Plan chỉ ghi "delete user" | Cleanup toàn bộ: files + Neo4j nodes + Qdrant points + Postgres cascade | An toàn cho dữ liệu y khoa, tránh orphan data |
| XSS fix iframe preview | Không có trong plan | `html.escape(filename)` | Lỗ hổng phát hiện khi review code, fix luôn |

**Bug đã fix:**

| Bug | Trigger | Fix |
|---|---|---|
| Rate limit không reset đúng giờ | Fixed window count theo phút | Sliding window counter qua Redis ZSET với TTL |
| TypeScript conflict React-Dropzone × Framer Motion | Type incompatibility giữa 2 lib khi animate dropzone | Tách prop spread, dùng `as any` ở junction (acceptable cho frontend animation layer) |

**Test coverage:** 13 unit tests (auth/document/query/rate_limit/security), all pass.

**Files Phase 4 đã tạo/sửa:**
- Backend: [admin/services.py](backend/src/mkge/application/admin/services.py), [rate_limit.py](backend/src/mkge/interface/api/rate_limit.py), [audit_repo.py](backend/src/mkge/infrastructure/db/postgres/audit_repo.py), [audit.py](backend/src/mkge/domain/value_objects/audit.py), [api/v1/admin.py](backend/src/mkge/interface/api/v1/admin.py), migration `f1b9b8a9183f_add_audit_logs.py`
- Frontend: [AdminPage.tsx](frontend/src/pages/AdminPage.tsx), [SettingsPage.tsx](frontend/src/pages/SettingsPage.tsx), [features/admin/](frontend/src/features/admin/) (StatsCards + UsersTable + AuditLogTable)
- Tests: [tests/unit/](backend/tests/unit/) (auth/document/query/rate_limiter/security)

---

*File này được generate từ session thiết kế kiến trúc ngày 2026-05-12.*
*Mọi thay đổi quyết định kỹ thuật → cập nhật file này.*
*Bản FINAL cập nhật 2026-05-25 sau khi merge phase4.*
*Lần cập nhật gần nhất: 2026-05-21 (close Phase 2).*
