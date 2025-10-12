# Devin: Shield AG-UI Code Development Assignment

**Date**: October 12, 2025  
**Project**: HX-Citadel Shield AG-UI  
**Your Role**: Code Development & GitHub Commits  
**Deployment**: Will be handled by HX team after your code is complete  
**Priority**: HIGH - Ready to begin

---

## 🎯 Your Scope: Code Development Only

### What You Will Do:
✅ Review all documentation  
✅ Create Ansible role structure  
✅ Write backend FastAPI code  
✅ Integrate frontend Vite + React code  
✅ Create Docker Compose configurations  
✅ Create Nginx configuration  
✅ Write all necessary templates and handlers  
✅ Commit all code to GitHub  
✅ Ensure code quality and completeness  

### What You Will NOT Do:
❌ Deploy to hx-dev-server (no network access)  
❌ Run Ansible playbooks (HX team will do this)  
❌ Test against live HX-Citadel services  
❌ Access internal network (192.168.10.x)  

### Handoff Point:
When you complete all code and commit to GitHub, the HX team will:
1. Review your code
2. Run the Ansible playbook on hx-test-server
3. Deploy to hx-dev-server (192.168.10.12)
4. Test against live services

---

## 📋 Your Task

Develop the complete Shield AG-UI application code using the **hybrid approach** (Vite + React + FastAPI + AG-UI Python SDK + Docker).

**Before starting implementation**, you must:
1. Review ALL documentation in the specified order
2. Understand the complete architecture and requirements
3. Confirm task scope and dependencies
4. Ask any clarifying questions
5. Get approval before beginning coding

---

## 📁 Documentation to Review

**Location**: `/home/agent0/hx-citadel-ansible/docs/Dev-Server-Configuration/`

### Review Order (FOLLOW THIS SEQUENCE):

#### Step 1: Start with README.md (5 minutes)
**File**: `README.md` (529 lines)

**What to understand**:
- Overall project vision
- Technology stack (Vite + React + FastAPI + Docker)
- Timeline (8 days)
- Budget ($12,000 approved)
- Document structure and navigation
- **Your role**: Code development, NOT deployment

**Key Question**: Do you understand the hybrid approach and that you're creating code for others to deploy?

---

#### Step 2: Review Stakeholder Decisions (10 minutes)
**File**: `STAKEHOLDER-DECISIONS-SUMMARY.md` (910 lines)

**What to understand**:
- All 10 stakeholder questions and answers
- Critical decisions (Auth, RBAC, retention)
- Permissions matrix (Admin/Contributor/Viewer)
- Performance targets (P95 ≤ 800ms @ 10 users)
- Browser support (Chrome + Edge, latest 2 versions)
- Accessibility requirements (WCAG 2.2 AA)

**Key Question**: Do you understand all the non-negotiable requirements your code must meet?

---

#### Step 3: Study Architecture (30 minutes)
**File**: `SHIELD-AG-UI-ARCHITECTURE.md` (2,201 lines, 21+ diagrams)

**What to understand**:
- 3-tier architecture (Vite SPA, FastAPI, Nginx)
- Docker Compose stack (3 containers)
- Redis Streams event bus architecture
- SSE (Server-Sent Events) for real-time updates
- Integration points with 7 HX-Citadel services:
  - hx-litellm-server:4000
  - hx-orchestrator-server:8000
  - hx-sqldb-server:6379 (Redis)
  - hx-vectordb-server:6333 (Qdrant)
  - hx-sqldb-server:5432 (PostgreSQL)
  - hx-ollama1/2
- Security architecture (4 layers)
- Authentication & RBAC flows

**Important**: These services exist but you won't access them. Write code that will connect to them when deployed.

**Key Questions**: 
- Do you understand how events flow from Redis → Backend → Frontend via SSE?
- Can you write code that connects to these services via environment variables?
- Do you understand the Docker networking setup?

---

#### Step 4: Review Specification (15 minutes)
**File**: `SHIELD-AG-UI-SPECIFICATION.md` (858 lines)

**What to understand**:
- 8 user scenarios with acceptance criteria
- 90 requirements (60 FR + 30 NFR)
- Success metrics and KPIs
- What's in scope vs out of scope

**Key Question**: Can you list the 9 pages that must be implemented and their main features?

---

#### Step 5: Study Implementation Plan (45 minutes)
**File**: `DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md` (2,086 lines)

**What to understand**:
- Complete Ansible role design (you create the role structure/files)
- Docker configuration details (you create docker-compose.yml)
- Code examples (Python + TypeScript)
- Frontend: How to integrate existing Vite app (6,500 LOC)
- Backend: How to build FastAPI with AG-UI Python SDK
- Testing strategy (unit tests you can write)
- SOLID principles application

**Key Questions**:
- Do you understand you're creating Ansible role FILES, not running them?
- Do you know where to clone the frontend from? (github.com/hanax-ai/citadel-shield-ui, feature-1 branch)
- Do you understand what needs to be removed (Supabase) and added (backend API client)?

---

#### Step 6: Review Task Breakdown (30 minutes)
**Directory**: `tasks/`

**Review in this order**:

**a) tasks/README.md** (335 lines)
- Master task index
- 16 total tasks (5 documented, 11 planned)
- Dependencies graph
- Parallel execution strategy
- Execution timeline

**b) tasks/T001-create-ansible-role.md** (273 lines)
- First task (1 hour effort)
- Create Ansible role structure
- 8 task files, templates, handlers
- **You create the directory structure and files**

**c) tasks/T002-backend-fastapi-app.md** (606 lines)
- Backend implementation (4 hours)
- FastAPI + AG-UI Python SDK
- Redis Streams consumer
- SSE endpoint
- Complete code examples
- **You write the Python code**

**d) tasks/T003-frontend-vite-integration.md** (708 lines)
- Frontend integration (2 hours)
- Clone existing citadel-shield-ui repository
- Remove Supabase dependencies
- Connect to FastAPI backend
- Fix CodeRabbit findings (15 issues)
- **You modify the existing code**

**e) tasks/T004-docker-compose-config.md** (401 lines)
- Docker Compose orchestration (2 hours)
- 3 services configuration
- Networks, volumes, health checks
- **You create docker-compose.yml and Dockerfiles**

**f) tasks/T005-nginx-reverse-proxy.md** (489 lines)
- Nginx configuration (1 hour)
- Reverse proxy setup
- SSL/TLS termination
- Route configuration
- **You create nginx.conf template**

---

## ✅ After Review: Your Deliverable

After completing the documentation review, **respond with**:

### 1. Confirmation Checklist
```
- [ ] I have read and understood README.md
- [ ] I have reviewed all stakeholder decisions
- [ ] I have studied the complete architecture (21+ diagrams)
- [ ] I have reviewed the specification (90 requirements)
- [ ] I have studied the implementation plan
- [ ] I have reviewed all 5 task documents (T001-T005)
- [ ] I understand the hybrid approach (existing Vite frontend + new FastAPI backend)
- [ ] I understand my role is CODE DEVELOPMENT ONLY (not deployment)
- [ ] I understand I'll commit to GitHub and HX team will deploy
- [ ] I know where to find the existing frontend code (citadel-shield-ui repo)
```

### 2. Architecture Understanding
Answer these questions:

**Q1**: What is the hybrid approach and why are we using it?

**Q2**: List the 3 Docker containers and their purposes.

**Q3**: What existing code are we reusing and where does it come from?

**Q4**: What needs to be written from scratch vs integrated?

**Q5**: How do events flow from Redis Streams to the frontend UI (describe the code you'll write)?

**Q6**: What are the 7 external HX-Citadel services your code will connect to?

### 3. Task Execution Understanding
Answer these questions:

**Q7**: What is the first task (T001) and what CODE will you create?

**Q8**: Which tasks can you work on in parallel?

**Q9**: What is the estimated total effort (hours) for all code development?

**Q10**: Where will you commit all your code?

**Q11**: What testing can you do locally vs what requires deployment?

### 4. Technical Clarifications
Answer these:

**Q12**: What needs to be removed from the existing frontend? (Hint: Supabase)

**Q13**: How many CodeRabbit findings need to be fixed in the frontend?

**Q14**: What Python SDK is used for the backend protocol?

**Q15**: What environment variables will your code use for service connections?

### 5. Development Workflow
Confirm understanding:

**Q16**: What is your deliverable? (Hint: Code in GitHub)

**Q17**: Who will run the Ansible playbook? (Hint: HX team)

**Q18**: Can you test against live HX-Citadel services? (Hint: No)

**Q19**: What branch will you commit to?

**Q20**: How will you hand off completed work to the HX team?

---

## 🚨 Before You Start Coding

**DO NOT BEGIN DEVELOPMENT** until you have:

1. ✅ Reviewed all documentation in the order specified above
2. ✅ Answered all 20 questions
3. ✅ Listed any questions or concerns you have
4. ✅ Received approval from the HX team to proceed

---

## 📝 Your Response Format

Please respond with:

```markdown
# Devin: Documentation Review Complete

## 1. Confirmation Checklist
[Check all boxes above]

## 2. Architecture Understanding
Q1: [Your answer]
Q2: [Your answer]
...
Q6: [Your answer]

## 3. Task Execution Understanding  
Q7: [Your answer]
...
Q11: [Your answer]

## 4. Technical Clarifications
Q12: [Your answer]
...
Q15: [Your answer]

## 5. Development Workflow
Q16: [Your answer]
...
Q20: [Your answer]

## 6. My Questions/Concerns
[List any questions or clarifications needed]

## 7. Development Approach
[Explain how you'll approach the development given you can't deploy]

## 8. Ready to Proceed
[YES/NO] - I am ready to begin coding T001

If NO, explain what additional information you need.
```

---

## 🎯 Success Criteria for This Review

You will be considered **ready to proceed** when:

1. ✅ All 20 questions answered correctly
2. ✅ You can explain the hybrid approach
3. ✅ You understand what to code vs what HX team will deploy
4. ✅ You know the GitHub workflow
5. ✅ You have NO blocking questions

---

## 📦 Your Deliverables (Code in GitHub)

### GitHub Repository Structure You'll Create:

```
hx-citadel-ansible/
├── roles/
│   └── shield_ag_ui/
│       ├── tasks/
│       │   ├── main.yml
│       │   ├── 01-prerequisites.yml
│       │   ├── 02-frontend-setup.yml
│       │   ├── 03-backend-setup.yml
│       │   ├── 04-docker-compose.yml
│       │   ├── 05-nginx-config.yml
│       │   ├── 06-systemd-services.yml
│       │   └── 07-validation.yml
│       ├── templates/
│       │   ├── docker-compose.yml.j2
│       │   ├── backend.Dockerfile.j2
│       │   ├── frontend.Dockerfile.j2
│       │   ├── nginx.conf.j2
│       │   ├── shield-backend.service.j2
│       │   ├── .env.backend.j2
│       │   └── .env.frontend.j2
│       ├── files/
│       │   ├── backend/ (FastAPI app)
│       │   │   ├── main.py
│       │   │   ├── redis_consumer.py
│       │   │   ├── sse_handler.py
│       │   │   ├── requirements.txt
│       │   │   └── ...
│       │   └── frontend/ (Modified citadel-shield-ui)
│       │       ├── src/
│       │       ├── public/
│       │       ├── package.json
│       │       └── ...
│       ├── handlers/
│       │   └── main.yml
│       ├── defaults/
│       │   └── main.yml
│       └── meta/
│           └── main.yml
└── playbooks/
    └── deploy-shield-ag-ui.yml (update existing)
```

### What You'll Commit:

1. **Ansible Role Structure** (T001)
   - All directories and skeleton files
   - Proper YAML formatting

2. **Backend Code** (T002)
   - `roles/shield_ag_ui/files/backend/`
   - FastAPI application
   - Redis Streams consumer
   - SSE handler
   - requirements.txt
   - All Python modules

3. **Frontend Code** (T003)
   - `roles/shield_ag_ui/files/frontend/`
   - Cloned from citadel-shield-ui (feature-1)
   - Supabase dependencies removed
   - Backend API client added
   - 15 CodeRabbit issues fixed
   - Updated package.json

4. **Docker Configurations** (T004)
   - `templates/docker-compose.yml.j2`
   - `templates/backend.Dockerfile.j2`
   - `templates/frontend.Dockerfile.j2`
   - Environment variable templates

5. **Nginx Configuration** (T005)
   - `templates/nginx.conf.j2`
   - SSL/TLS configuration
   - Reverse proxy rules

6. **Ansible Task Files** (T001)
   - All task YAML files
   - Handlers
   - Defaults
   - Meta information

7. **Documentation**
   - README for the role
   - Deployment instructions for HX team
   - Environment variable documentation

---

## 🔄 Development Workflow

### Your Process:

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/shield-ag-ui-devin-implementation
   ```

2. **Develop Code** (Tasks T001-T005)
   - Write Ansible role structure
   - Develop backend FastAPI code
   - Integrate frontend code
   - Create Docker configurations
   - Create Nginx configuration

3. **Local Validation** (What you CAN do)
   - ✅ Python syntax checking
   - ✅ TypeScript/JavaScript linting
   - ✅ YAML validation
   - ✅ Docker Compose syntax
   - ✅ Unit tests (mock services)
   - ✅ Code quality checks

4. **Cannot Test** (Requires deployment)
   - ❌ Connection to real Redis
   - ❌ Connection to real Orchestrator
   - ❌ Connection to real Qdrant/PostgreSQL
   - ❌ End-to-end user flows
   - ❌ SSE streaming from real events

5. **Commit & Push**
   ```bash
   git add roles/shield_ag_ui/
   git commit -m "feat: implement Shield AG-UI code (T001-T005)"
   git push origin feature/shield-ag-ui-devin-implementation
   ```

6. **Create Pull Request**
   - Title: "Shield AG-UI Implementation (Devin)"
   - Description: List what was implemented
   - Tag: HX team for review

7. **Handoff to HX Team**
   - They review code
   - They run playbook on hx-test-server
   - They deploy to hx-dev-server
   - They test against live services

---

## 🧪 Testing Strategy (Your Scope)

### What You Should Test:

#### 1. Syntax & Linting
```bash
# Python
python -m py_compile roles/shield_ag_ui/files/backend/**/*.py
ruff check roles/shield_ag_ui/files/backend/

# TypeScript/JavaScript
cd roles/shield_ag_ui/files/frontend/
npm run lint

# YAML
yamllint roles/shield_ag_ui/

# Ansible
ansible-lint roles/shield_ag_ui/
```

#### 2. Unit Tests (Mock Services)
```python
# Example: Test backend with mocked Redis
@pytest.fixture
def mock_redis():
    return MagicMock()

def test_redis_consumer(mock_redis):
    consumer = RedisConsumer(mock_redis)
    # Test logic without real Redis
```

#### 3. Docker Build Tests
```bash
# Test Docker builds (don't run)
cd roles/shield_ag_ui/templates/
docker build -f backend.Dockerfile.j2 --no-cache .
docker build -f frontend.Dockerfile.j2 --no-cache .
```

### What HX Team Will Test:

- Ansible playbook execution
- Deployment to hx-dev-server
- Connection to live services
- End-to-end user scenarios
- Performance under load
- Security scanning

---

## 📞 Support

If you need clarification during review:
- Ask specific questions about any section
- Request diagrams or examples
- Confirm your understanding before proceeding
- Ask about environment variables and service connections

**Remember**: Your code must be deployment-ready even though you won't deploy it.

---

## 🚀 After Approval

Once you answer all questions and get approval, you will:

### Development Sequence:

**Phase 1: Foundation (2 hours)**
1. T001: Create Ansible role structure
   - All directories
   - Skeleton YAML files
   - Commit to GitHub

**Phase 2: Core Development (6 hours)**
2. T002: Backend FastAPI code
   - All Python modules
   - Redis consumer
   - SSE handler
   - Unit tests
   - Commit to GitHub

3. T003: Frontend integration (parallel with T002)
   - Clone citadel-shield-ui
   - Remove Supabase
   - Add backend client
   - Fix 15 CodeRabbit issues
   - Commit to GitHub

**Phase 3: Infrastructure (3 hours)**
4. T004: Docker configurations
   - docker-compose.yml template
   - Dockerfiles
   - Environment templates
   - Commit to GitHub

5. T005: Nginx configuration (parallel with T004)
   - nginx.conf template
   - SSL/TLS setup
   - Reverse proxy rules
   - Commit to GitHub

**Phase 4: Finalization (1 hour)**
6. Documentation
   - Role README
   - Deployment guide
   - Variable documentation
   - Commit to GitHub

7. Pull Request
   - Create PR
   - Add description
   - Tag HX team

**Estimated timeline**: 12 hours development + HX team deployment

---

## ✅ Final Checklist Before Handoff

Before creating your PR, ensure:

```
- [ ] All code committed to feature branch
- [ ] All files in correct directory structure
- [ ] Python code passes syntax checks
- [ ] TypeScript code passes linting
- [ ] YAML files are valid
- [ ] Docker files can build
- [ ] Unit tests pass (with mocks)
- [ ] No hardcoded credentials
- [ ] Environment variables documented
- [ ] README created for role
- [ ] Deployment instructions written
- [ ] Pull request created
- [ ] HX team tagged for review
```

---

**Start your review with README.md and work through the sequence.**

**Remember**: You're creating production-ready CODE that others will DEPLOY.

**Good luck! 🚀**

