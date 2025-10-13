# Devin: Scope Correction - Dev-Server Setup ONLY

**Date**: October 13, 2025  
**IMPORTANT UPDATE**: Your scope is dev-server infrastructure ONLY (no frontend work)

---

## 🎯 **Updated Scope: T001, T002, T004, T005 ONLY**

### ✅ **What You WILL Do** (8 hours):

**T001: Ansible Role Structure** (1 hour)
- Create `roles/shield_ag_ui/` directory structure
- Write all Ansible task YAML files
- Write defaults, handlers, meta
- Commit to GitHub

**T002: Backend FastAPI Application** (4 hours)
- Write complete FastAPI backend code
- Redis Streams consumer
- SSE event handler
- AG-UI protocol implementation
- Unit tests (mocked services)
- requirements.txt
- Commit to GitHub

**T004: Docker Compose Configuration** (2 hours)
- docker-compose.yml.j2 template
- backend.Dockerfile.j2
- frontend.Dockerfile.j2 (generic Vite build - NO code modifications)
- Environment variable templates
- Commit to GitHub

**T005: Nginx Reverse Proxy** (1 hour)
- nginx.conf.j2 template
- Reverse proxy routes
- SSL/TLS configuration
- Commit to GitHub

**Total Effort**: 8 hours

---

### ❌ **What You Will NOT Do**:

**T003: Frontend Integration** - **REMOVED FROM YOUR SCOPE**
- ❌ NOT cloning citadel-shield-ui
- ❌ NOT removing Supabase
- ❌ NOT adding backend API client
- ❌ NOT fixing 15 CodeRabbit issues
- ❌ NOT modifying any frontend TypeScript code

**Reason**: A separate Frontend AI will handle ALL frontend work independently.

**T006-T016**: Still out of scope (HX team post-deployment)

---

## 🔄 **Updated Workflow**

### Your Work (Dev-Server Infrastructure):
```
You (Devin):
├── T001: Create Ansible role (1h)
├── T002: Write backend FastAPI (4h)
├── T004: Create Docker configs (2h)
└── T005: Create Nginx config (1h)
Total: 8 hours
```

### Frontend AI's Work (Separately):
```
Frontend AI:
└── T003: Frontend modifications (2h)
    ├── Clone citadel-shield-ui
    ├── Remove Supabase
    ├── Add backend client
    └── Fix 15 CodeRabbit issues
```

### Integration Point:
Both will commit to GitHub, then HX team will:
1. Merge both branches
2. Deploy combined code to hx-dev-server

---

## 📋 **Updated Checklist (8 Hours)**

### T001: Ansible Role Structure (1 hour)
```
- [ ] Create roles/shield_ag_ui/ directory
- [ ] Create subdirectories (tasks, templates, files, handlers, defaults, meta)
- [ ] Write tasks/main.yml
- [ ] Write tasks/01-prerequisites.yml
- [ ] Write tasks/02-backend-setup.yml (backend only, no frontend)
- [ ] Write tasks/03-docker-compose.yml
- [ ] Write tasks/04-nginx-config.yml
- [ ] Write tasks/05-systemd-services.yml
- [ ] Write tasks/06-validation.yml
- [ ] Write defaults/main.yml (all variables)
- [ ] Write handlers/main.yml
- [ ] Write meta/main.yml
- [ ] Create README.md
- [ ] Validate with ansible-lint
- [ ] Commit to GitHub
```

### T002: Backend FastAPI (4 hours)
```
- [ ] Create roles/shield_ag_ui/files/backend/
- [ ] Write main.py (FastAPI app)
- [ ] Write config.py (settings management)
- [ ] Write routers/events.py (SSE endpoint)
- [ ] Write routers/api.py (REST endpoints)
- [ ] Write services/redis_consumer.py (Redis Streams)
- [ ] Write services/sse_handler.py (SSE streaming)
- [ ] Write services/agui_protocol.py (AG-UI transformations)
- [ ] Write models/events.py (Pydantic models)
- [ ] Write requirements.txt
- [ ] Write tests/ (unit tests with mocks)
- [ ] Validate Python syntax (mypy, ruff)
- [ ] Commit to GitHub
```

### T004: Docker Compose (2 hours)
```
- [ ] Create templates/docker-compose.yml.j2
      Services:
      - frontend (port 3001:3000) - generic Vite container
      - backend (port 8001:8000) - your FastAPI code
      - nginx (ports 80, 443)
- [ ] Create templates/backend.Dockerfile.j2
      Multi-stage build for your FastAPI app
- [ ] Create templates/frontend.Dockerfile.j2
      Generic Vite build (npm install && npm run build)
      NO frontend code modifications needed
- [ ] Create templates/.env.backend.j2
      All backend environment variables
- [ ] Create templates/.env.frontend.j2
      VITE_BACKEND_URL only
- [ ] Validate Docker Compose syntax
- [ ] Commit to GitHub
```

### T005: Nginx Config (1 hour)
```
- [ ] Create templates/nginx.conf.j2
- [ ] Configure upstreams:
      upstream frontend { server frontend:3000; }
      upstream backend { server backend:8000; }
- [ ] Configure routes:
      location / → frontend
      location /api/ → backend
      location /events → backend (SSE, disable buffering)
- [ ] Configure SSL/TLS
- [ ] Add security headers
- [ ] Add rate limiting
- [ ] Validate Nginx config syntax
- [ ] Commit to GitHub
```

### Final Steps
```
- [ ] Run ansible-lint on all YAML
- [ ] Run mypy/ruff on Python backend code
- [ ] Test Docker builds (backend only)
- [ ] Verify no secrets committed
- [ ] Create Pull Request: "Dev-Server Infrastructure (T001, T002, T004, T005)"
- [ ] Note in PR: "Frontend work (T003) handled separately by Frontend AI"
- [ ] Tag @hanax-ai for review
```

---

## 📚 **Updated Required Reading**

**REMOVED** from your reading list:
- ~~FRONTEND_SUPABASE_REMOVAL_GUIDE.md~~ (Frontend AI will use this)

**KEEP** in your reading list:
1. ✅ **DEVIN_REVIEW_AND_APPROVAL.md** (your approval + corrections)
2. ✅ **DEVIN_QUESTIONS_ANSWERED.md** (focus on role name, scope, CodeRabbit summary only - skip frontend details)
3. ✅ **tasks/T001-create-ansible-role.md** (role structure)
4. ✅ **tasks/T002-backend-fastapi-app.md** (backend implementation)
5. ✅ **tasks/T004-docker-compose-config.md** (Docker configs)
6. ✅ **tasks/T005-nginx-reverse-proxy.md** (Nginx config)

**SKIP** these (not your scope):
- ❌ FRONTEND_SUPABASE_REMOVAL_GUIDE.md (Frontend AI's work)
- ❌ tasks/T003-frontend-vite-integration.md (Frontend AI's work)

---

## 🔧 **Updated T004: Frontend Dockerfile**

Since you're NOT modifying frontend code, your frontend Dockerfile is simple:

**File**: `templates/frontend.Dockerfile.j2`

```dockerfile
# Generic Vite build - NO code modifications
FROM node:20-alpine AS builder

WORKDIR /app

# Copy frontend code (already modified by Frontend AI)
COPY files/frontend/ .

# Install dependencies and build
RUN npm ci
RUN npm run build

# Production server
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**Note**: You just build whatever frontend code exists in `files/frontend/`. The Frontend AI will have already modified it.

---

## 🤝 **Coordination with Frontend AI**

### Scenario 1: Frontend AI Completes First
1. Frontend AI modifies citadel-shield-ui
2. Frontend AI commits to `feature/frontend-backend-integration`
3. **You**: Reference that frontend code in your Ansible role
4. **You**: Your Dockerfile just builds it (no modifications)

### Scenario 2: You Complete First
1. **You**: Create generic frontend Dockerfile (just runs `npm run build`)
2. **You**: Leave `files/frontend/` empty with a README:
   ```
   # Frontend Code - To Be Added
   This directory will contain the modified frontend from the Frontend AI.
   The Dockerfile is ready to build whatever is placed here.
   ```
3. Frontend AI adds their code later
4. HX team merges both

### Recommended: **You work in parallel**
- **You**: Focus on backend, Docker, Nginx, Ansible
- **Frontend AI**: Focus on frontend modifications
- **HX team**: Merges both when complete

---

## ✅ **Updated Success Criteria**

You're ready to proceed when you can answer:

✅ What is your scope? → **T001, T002, T004, T005 (NO T003)**  
✅ What is the role name? → **shield_ag_ui**  
✅ What is the backend port? → **8001**  
✅ Do you modify frontend code? → **NO (Frontend AI does)**  
✅ What does your frontend Dockerfile do? → **Generic build (npm ci && npm run build)**  
✅ What is your deliverable? → **Dev-server infrastructure code**

---

## 📊 **Revised Effort Estimate**

**Original**: 10 hours (T001-T005)  
**Updated**: 8 hours (T001, T002, T004, T005)  
**Removed**: 2 hours (T003 - Frontend AI's work)

| Task | Your Work | Effort |
|------|-----------|--------|
| T001 | Ansible role structure | 1h |
| T002 | Backend FastAPI | 4h |
| ~~T003~~ | ~~Frontend integration~~ | ~~2h~~ |
| T004 | Docker Compose | 2h |
| T005 | Nginx config | 1h |
| **Total** | **Dev-server setup** | **8h** |

---

## 🚀 **Next Steps**

1. **Acknowledge** this scope correction
2. **Read** the updated required documents (skip frontend guide)
3. **Begin T001**: Create `roles/shield_ag_ui/`
4. **Work through**: T001 → T002 → T004 → T005
5. **Commit**: Feature branch for dev-server infrastructure
6. **PR**: Tag as "Dev-Server Infrastructure (Backend + Docker + Nginx)"

---

## 💬 **Response Template**

Please confirm:

```
✅ I understand my scope is T001, T002, T004, T005 ONLY
✅ I will NOT do T003 (frontend work)
✅ Frontend AI will handle all frontend modifications separately
✅ My focus: Backend FastAPI + Docker + Nginx + Ansible
✅ Updated effort: 8 hours (not 10)
✅ Ready to begin T001: Create roles/shield_ag_ui/
```

---

**Your scope is now clear: Dev-server infrastructure only, no frontend modifications!**

**Good luck! 🚀**

