# Devin: Shield AG-UI Implementation Assignment

**Date**: October 12, 2025  
**Project**: HX-Citadel Shield AG-UI  
**Assignment**: Review documentation and prepare for implementation  
**Priority**: HIGH - Ready to begin

---

## 📋 Your Task

You are assigned to implement the Shield AG-UI application on hx-dev-server using the **hybrid approach** (Vite + React + FastAPI + AG-UI Python SDK + Docker).

**Before starting implementation**, you must:
1. Review ALL documentation in the specified order
2. Understand the complete architecture and requirements
3. Confirm task scope and dependencies
4. Ask any clarifying questions
5. Get approval before beginning implementation

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

**Key Question**: Do you understand the hybrid approach and why we're using existing frontend code?

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

**Key Question**: Do you understand all the non-negotiable requirements and constraints?

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

**Key Questions**: 
- Do you understand how events flow from Redis → Backend → Frontend via SSE?
- Can you explain the data flow for a web crawl operation?
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
- Complete Ansible role design
- Docker configuration details
- Code examples (Python + TypeScript)
- Frontend: How to integrate existing Vite app (6,500 LOC)
- Backend: How to build FastAPI with AG-UI Python SDK
- Testing strategy (unit, integration, E2E)
- SOLID principles application

**Key Questions**:
- Do you understand the frontend is EXISTING code that needs integration, not new development?
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

**c) tasks/T002-backend-fastapi-app.md** (606 lines)
- Backend implementation (4 hours)
- FastAPI + AG-UI Python SDK
- Redis Streams consumer
- SSE endpoint
- Complete code examples

**d) tasks/T003-frontend-vite-integration.md** (708 lines)
- Frontend integration (2 hours - REDUCED from 6h)
- Clone existing citadel-shield-ui repository
- Remove Supabase dependencies
- Connect to FastAPI backend
- Fix CodeRabbit findings (15 issues)

**e) tasks/T004-docker-compose-config.md** (401 lines)
- Docker Compose orchestration (2 hours)
- 3 services configuration
- Networks, volumes, health checks

**f) tasks/T005-nginx-reverse-proxy.md** (489 lines)
- Nginx configuration (1 hour)
- Reverse proxy setup
- SSL/TLS termination
- Route configuration

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
- [ ] I understand the 16-task execution plan
- [ ] I understand the parallel execution opportunities
- [ ] I know where to find the existing frontend code (citadel-shield-ui repo)
```

### 2. Architecture Understanding
Answer these questions:

**Q1**: What is the hybrid approach and why are we using it?

**Q2**: List the 3 Docker containers and their purposes.

**Q3**: What existing code are we reusing and where does it come from?

**Q4**: What needs to be built from scratch vs integrated?

**Q5**: How do events flow from Redis Streams to the frontend UI?

**Q6**: What are the 7 external HX-Citadel services we integrate with?

### 3. Task Execution Understanding
Answer these questions:

**Q7**: What is the first task (T001) and how long should it take?

**Q8**: Which tasks can run in parallel?

**Q9**: What is the estimated total effort (hours) for all tasks?

**Q10**: What is the target completion timeline?

**Q11**: What testing approach should be used (TDD)?

### 4. Technical Clarifications
Answer these:

**Q12**: What needs to be removed from the existing frontend? (Hint: Supabase)

**Q13**: How many CodeRabbit findings need to be fixed in the frontend?

**Q14**: What Python SDK is used for the backend protocol?

**Q15**: What port does the frontend run on? Backend? Nginx?

### 5. Critical Requirements
Confirm understanding:

**Q16**: What are the performance SLOs (P95 latency)?

**Q17**: What are the 3 RBAC roles?

**Q18**: What browsers must be supported?

**Q19**: What accessibility level is required?

**Q20**: Where is the target deployment server (hostname + IP)?

---

## 🚨 Before You Start Implementation

**DO NOT BEGIN CODING** until you have:

1. ✅ Reviewed all documentation in the order specified above
2. ✅ Answered all 20 questions
3. ✅ Listed any questions or concerns you have
4. ✅ Received approval from the team to proceed

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

## 5. Critical Requirements
Q16: [Your answer]
...
Q20: [Your answer]

## 6. My Questions/Concerns
[List any questions or clarifications needed]

## 7. Ready to Proceed
[YES/NO] - I am ready to begin implementation of T001

If NO, explain what additional information you need.
```

---

## 🎯 Success Criteria for This Review

You will be considered **ready to proceed** when:

1. ✅ All 20 questions answered correctly
2. ✅ You can explain the hybrid approach
3. ✅ You understand task dependencies
4. ✅ You know what to build vs what to integrate
5. ✅ You have NO blocking questions

---

## 📞 Support

If you need clarification during review:
- Ask specific questions about any section
- Request diagrams or examples
- Confirm your understanding before proceeding

**Remember**: Taking time to understand NOW saves debugging time LATER.

---

## 🚀 After Approval

Once you answer all questions and get approval, you will:
1. Begin with T001 (Create Ansible role - 1 hour)
2. Then T002 + T003 in parallel (Backend + Frontend - 6 hours)
3. Then T004 + T005 (Docker + Nginx - 3 hours)
4. Continue through remaining tasks

**Estimated timeline**: 8 days (Oct 12-20, 2025)

---

**Start your review with README.md and work through the sequence.**

**Good luck! 🚀**

