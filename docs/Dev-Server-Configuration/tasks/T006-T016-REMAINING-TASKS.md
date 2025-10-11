# Remaining Tasks: T006-T016

**Created**: October 11, 2025  
**Status**: Ready for Implementation  
**Total Tasks**: 11  
**Total Effort**: 28 hours  
**Team**: 2-3 developers

---

## Overview

This document provides comprehensive breakdowns for the **remaining 11 tasks** (T006-T016) needed to complete the Shield AG-UI implementation. Each task includes:

- Detailed description and scope
- Key deliverables and code structure
- Acceptance criteria
- Testing approach
- Estimated effort

**Use this document as a guide to create individual task files when ready to execute.**

---

##  T006: Unit Tests for Backend Services

**Phase**: 3.2 Tests First (TDD)  
**Parallel**: [P] Can run with T007-T009  
**Estimated Effort**: 3 hours  
**Prerequisites**: T001 (Ansible role structure)

### Description

Create comprehensive unit tests for all backend services using pytest. Tests should be written **BEFORE** implementation (TDD) and must initially FAIL.

### Key Deliverables

**Directory Structure**:
```
backend/tests/unit/
├── __init__.py
├── conftest.py
├── test_auth_service.py
├── test_rbac_service.py
├── test_event_service.py
├── test_redis_consumer.py
├── test_litellm_client.py
└── test_audit_logger.py
```

**Test Coverage**:
- `test_auth_service.py`: User registration, login, password reset, MFA enrollment
- `test_rbac_service.py`: Permission checks, role validation, scope enforcement
- `test_event_service.py`: Redis→AG-UI event transformation
- `test_redis_consumer.py`: Stream consumption, acknowledgment, reconnection
- `test_litellm_client.py`: Tool execution proxy, error handling
- `test_audit_logger.py`: Event logging, tamper-evident storage

**Example Test** (`test_auth_service.py`):
```python
import pytest
from src.services.auth_service import AuthService
from src.models.user import User

@pytest.fixture
def auth_service():
    return AuthService()

def test_register_user_success(auth_service):
    """Test successful user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }
    
    user = auth_service.register(user_data)
    
    assert user.email == "test@example.com"
    assert user.password_hash != "SecurePass123!"  # Should be hashed
    assert user.email_verified == False
    
def test_register_user_weak_password(auth_service):
    """Test registration with weak password should fail"""
    user_data = {
        "email": "test@example.com",
        "password": "weak",  # Too short
        "full_name": "Test User"
    }
    
    with pytest.raises(ValueError, match="Password too weak"):
        auth_service.register(user_data)

def test_login_success(auth_service):
    """Test successful login"""
    # Setup
    user = auth_service.register({
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    user.email_verified = True
    
    # Test
    token = auth_service.login("test@example.com", "SecurePass123!")
    
    assert token is not None
    assert len(token) > 0
    
def test_login_wrong_password(auth_service):
    """Test login with wrong password increments failed attempts"""
    # Setup
    user = auth_service.register({
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    user.email_verified = True
    
    # Test
    with pytest.raises(AuthenticationError):
        auth_service.login("test@example.com", "WrongPassword")
    
    assert user.failed_login_attempts == 1
```

### Acceptance Criteria

- [ ] All service classes have corresponding test files
- [ ] Test coverage > 80% for services
- [ ] Tests use pytest fixtures for setup
- [ ] Tests use mocks for external dependencies (Redis, DB, HTTP)
- [ ] Tests initially FAIL (TDD)
- [ ] All tests pass after implementation
- [ ] Tests run in < 10 seconds
- [ ] Tests are isolated (no shared state)

### Testing Tools

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking support
- `faker`: Test data generation

**Run Tests**:
```bash
cd backend/
pytest tests/unit/ -v --cov=src/services --cov-report=html
```

---

## T007: Integration Tests for API Endpoints

**Phase**: 3.2 Tests First (TDD)  
**Parallel**: [P] Can run with T006, T008, T009  
**Estimated Effort**: 3 hours  
**Prerequisites**: T001

### Description

Create integration tests for all API endpoints using FastAPI TestClient. Tests full request/response cycle including authentication, RBAC, and database operations.

### Key Deliverables

**Test Structure**:
```
backend/tests/integration/
├── __init__.py
├── conftest.py
├── test_api_auth.py
├── test_api_tools.py
├── test_api_jobs.py
├── test_api_admin.py
└── test_sse_events.py
```

**Example Test** (`test_api_auth.py`):
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_register_endpoint():
    """Test POST /auth/register"""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    
    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.json()["email"] == "test@example.com"

def test_login_endpoint():
    """Test POST /auth/login"""
    # Setup: Register user first
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    
    # Test login
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    
def test_crawl_endpoint_requires_auth():
    """Test POST /api/crawl requires authentication"""
    response = client.post("/api/crawl", json={
        "url": "https://example.com"
    })
    
    assert response.status_code == 401
```

### Acceptance Criteria

- [ ] All API endpoints have integration tests
- [ ] Tests cover happy path and error cases
- [ ] Authentication/authorization tested
- [ ] Database transactions tested
- [ ] Tests use test database (not production)
- [ ] Tests clean up after themselves
- [ ] All tests pass after implementation

---

## T008: E2E Tests with Playwright

**Phase**: 3.2 Tests First (TDD)  
**Parallel**: [P] Can run with T006, T007, T009  
**Estimated Effort**: 4 hours  
**Prerequisites**: T001

### Description

Create end-to-end tests using Playwright to test the complete user journey from browser perspective. Tests critical user flows including authentication, crawling, graph visualization, and job tracking.

### Key Deliverables

**Test Structure**:
```
frontend/tests/e2e/
├── fixtures/
│   ├── auth.ts
│   └── test-data.ts
├── auth.spec.ts
├── crawl-workflow.spec.ts
├── graph-visualization.spec.ts
└── job-tracking.spec.ts
```

**Example Test** (`auth.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can register and login', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3001');
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
    
    // Click register
    await page.click('text=Register');
    
    // Fill registration form
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.fill('[name="fullName"]', 'Test User');
    await page.click('button[type="submit"]');
    
    // Should show success message
    await expect(page.locator('text=Registration successful')).toBeVisible();
    
    // Login
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome, Test User')).toBeVisible();
  });
  
  test('login fails with wrong password', async ({ page }) => {
    await page.goto('http://localhost:3001/login');
    
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'WrongPassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});

test.describe('Web Crawl Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('http://localhost:3001/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);
  });
  
  test('user can initiate web crawl and see progress', async ({ page }) => {
    // Open crawl dialog
    await page.click('button:has-text("Crawl Web")');
    
    // Fill URL
    await page.fill('[name="url"]', 'https://example.com');
    await page.fill('[name="maxPages"]', '10');
    await page.click('button:has-text("Start Crawl")');
    
    // Should see job submitted message
    await expect(page.locator('text=Job submitted')).toBeVisible();
    
    // Should see job ID
    await expect(page.locator('[data-testid="job-id"]')).toBeVisible();
    
    // Should see progress updates in event timeline
    await expect(page.locator('[data-testid="event-timeline"]')).toBeVisible();
    await expect(page.locator('text=Crawling')).toBeVisible({ timeout: 10000 });
  });
});
```

### Acceptance Criteria

- [ ] Critical user flows tested (auth, crawl, query, viz)
- [ ] Tests run in headless browser
- [ ] Tests use test environment (not production)
- [ ] Screenshots captured on failure
- [ ] Tests wait for async operations (SSE events)
- [ ] All tests pass in CI/CD pipeline

**Run Tests**:
```bash
cd frontend/
npx playwright test
npx playwright test --ui  # Interactive mode
npx playwright show-report  # View results
```

---

## T009: Contract Tests for AG-UI Protocol

**Phase**: 3.2 Tests First (TDD)  
**Parallel**: [P] Can run with T006-T008  
**Estimated Effort**: 2 hours  
**Prerequisites**: T001

### Description

Create contract tests to ensure backend correctly implements the AG-UI protocol. Tests validate event structure, SSE format, and protocol compliance.

### Key Deliverables

```
backend/tests/contract/
├── __init__.py
├── test_ag_ui_events.py
└── test_sse_format.py
```

**Example Test** (`test_ag_ui_events.py`):
```python
import pytest
from src.services.event_service import EventService
from ag_ui.core import TextMessageContentEvent, ToolCallEvent

def test_text_message_content_event_structure():
    """Test TextMessageContentEvent matches AG-UI spec"""
    event = TextMessageContentEvent(
        messageId="msg_123",
        delta="Processing chunk 1/10"
    )
    
    # Validate structure
    assert event.type == "TEXT_MESSAGE_CONTENT"
    assert hasattr(event, "messageId")
    assert hasattr(event, "delta")
    assert isinstance(event.delta, str)
    
def test_tool_call_event_structure():
    """Test ToolCallEvent matches AG-UI spec"""
    event = ToolCallEvent(
        messageId="msg_123",
        toolCallId="tool_456",
        toolName="crawl_web",
        args={"url": "https://example.com"}
    )
    
    assert event.type == "TOOL_CALL"
    assert event.toolName == "crawl_web"
    assert isinstance(event.args, dict)
```

### Acceptance Criteria

- [ ] All AG-UI event types tested
- [ ] Event serialization tested
- [ ] SSE format validated
- [ ] Protocol version compatibility tested

---

## T010: Implement Authentication Service

**Phase**: 3.4 Integration  
**Parallel**: No  
**Estimated Effort**: 3 hours  
**Prerequisites**: T002 (Backend), T007 (Integration tests)

### Description

Implement the authentication service with user registration, login, password reset, and MFA enrollment hooks. Must pass all tests from T007.

### Key Deliverables

```python
# src/services/auth_service.py
class AuthService:
    def register(self, data: RegisterRequest) -> User:
        """Register new user with email verification"""
        # Validate password strength
        # Hash password with bcrypt
        # Create user record
        # Send verification email
        # Log audit event
        pass
    
    def login(self, email: str, password: str) -> AccessToken:
        """Login user and return JWT token"""
        # Verify email/password
        # Check account not locked
        # Generate JWT token
        # Log audit event
        pass
    
    def reset_password(self, email: str) -> None:
        """Send password reset email"""
        pass
    
    def change_password(self, user_id: str, old: str, new: str) -> None:
        """Change user password"""
        # Invalidate all sessions
        pass
```

### Acceptance Criteria

- [ ] User registration works with email verification
- [ ] Login returns valid JWT token
- [ ] Password hashed with bcrypt (cost factor 12)
- [ ] Account lockout after 5 failed attempts
- [ ] Password policy enforced (12+ chars, complexity)
- [ ] MFA enrollment hooks present (disabled initially)
- [ ] All audit events logged
- [ ] All integration tests pass

---

## T011: Implement RBAC Service

**Phase**: 3.4 Integration  
**Parallel**: No  
**Estimated Effort**: 2 hours  
**Prerequisites**: T010 (Authentication service)

### Description

Implement Role-Based Access Control with 3 roles (Admin, Contributor, Viewer) and workspace/project scoping.

### Key Deliverables

```python
# src/services/rbac_service.py
class RBACService:
    def check_permission(
        self, 
        user: User, 
        action: str, 
        resource: str,
        workspace_id: Optional[str] = None
    ) -> bool:
        """Check if user has permission for action on resource"""
        # Load user role
        # Check workspace/project scope
        # Validate permission
        pass
    
    def assign_role(
        self,
        user_id: str,
        role: Role,
        scope: Scope
    ) -> None:
        """Assign role to user with scope"""
        # Log audit event
        pass
```

**Permissions Matrix**:
```python
PERMISSIONS = {
    "Admin": ["*"],  # All permissions
    "Contributor": [
        "dashboard:view",
        "query:execute",
        "crawl:execute",
        "ingest:execute",
        "graph:view",
        "job:view:own",
    ],
    "Viewer": [
        "dashboard:view",
        "query:execute",
        "graph:view",
        "job:view:own",
    ]
}
```

### Acceptance Criteria

- [ ] 3 roles implemented (Admin, Contributor, Viewer)
- [ ] Workspace/project scoping works
- [ ] Permission checks on all endpoints
- [ ] UI hides unauthorized features
- [ ] Admin can manage roles via UI
- [ ] All role changes logged to audit log

---

## T012: Implement Audit Logging

**Phase**: 3.5 Polish  
**Parallel**: [P] Can run with T013  
**Estimated Effort**: 2 hours  
**Prerequisites**: T002 (Backend)

### Description

Implement comprehensive audit logging with tamper-evident storage (append-only + hash chaining).

### Key Deliverables

```python
# src/services/audit_logger.py
class AuditLogger:
    def log(self, event: AuditEvent) -> None:
        """Log audit event with hash chain"""
        # Get previous event hash
        # Calculate current event hash
        # Append to audit log
        # Store hash chain
        pass
    
    def export(self, start_date: date, end_date: date) -> str:
        """Export audit log as CSV/JSON"""
        pass
    
    def verify_integrity(self) -> bool:
        """Verify hash chain integrity"""
        pass
```

**Event Categories**:
- Auth: login, logout, password_change, account_locked
- Access: role_assigned, permission_denied
- Data: file_uploaded, file_deleted, kg_entity_modified
- System: config_changed, rate_limit_triggered

### Acceptance Criteria

- [ ] All event categories logged
- [ ] Tamper-evident storage (hash chaining)
- [ ] 90-day retention enforced
- [ ] Export to CSV/JSON (Admin only)
- [ ] Hash chain integrity verifiable

---

## T013: Implement Chunked Upload

**Phase**: 3.5 Polish  
**Parallel**: [P] Can run with T012  
**Estimated Effort**: 3 hours  
**Prerequisites**: T002 (Backend)

### Description

Implement chunked/resumable file uploads for 100MB+ files with virus scanning and background processing.

### Key Deliverables

```python
# src/routers/api.py
@router.post("/upload/init")
async def init_upload(request: InitUploadRequest):
    """Initialize chunked upload session"""
    # Generate upload_id
    # Store upload metadata
    # Return upload URLs
    pass

@router.put("/upload/{upload_id}/chunk/{chunk_num}")
async def upload_chunk(upload_id: str, chunk_num: int, file: UploadFile):
    """Upload a single chunk"""
    # Validate chunk
    # Store chunk
    # Update progress
    pass

@router.post("/upload/{upload_id}/complete")
async def complete_upload(upload_id: str):
    """Complete upload and start processing"""
    # Verify all chunks received
    # Combine chunks
    # Verify checksum
    # Virus scan
    # Enqueue processing job
    pass
```

### Acceptance Criteria

- [ ] Supports 100MB+ files
- [ ] 5MB chunk size
- [ ] Resume after disconnect
- [ ] Virus scanning before processing
- [ ] Progress UI (pause/cancel/resume)
- [ ] Storage quotas enforced
- [ ] All uploads logged to audit log

---

## T014: Create Ansible Deployment Playbook

**Phase**: 3.5 Polish  
**Parallel**: No  
**Estimated Effort**: 2 hours  
**Prerequisites**: T001-T005 (All infrastructure tasks)

### Description

Create the main Ansible playbook that orchestrates the complete AG-UI deployment using the `ag_ui_deployment` role.

### Key Deliverables

```yaml
# playbooks/deploy-ag-ui.yml
---
- name: Deploy Shield AG-UI to dev-server
  hosts: dev_servers
  become: true
  gather_facts: true
  
  vars:
    ag_ui_env: "development"
    ag_ui_frontend_port: 3001
    ag_ui_backend_port: 8002
  
  pre_tasks:
    - name: Verify target server
      ansible.builtin.assert:
        that:
          - ansible_hostname == "hx-dev-server"
          - ansible_distribution == "Ubuntu"
          - ansible_distribution_version >= "24.04"
        fail_msg: "Wrong server or OS version"
    
    - name: Display deployment banner
      ansible.builtin.debug:
        msg: |
          ╔════════════════════════════════════════╗
          ║  Shield AG-UI Deployment Starting      ║
          ╠════════════════════════════════════════╣
          ║  Target: {{ ansible_hostname }}
          ║  OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
          ║  Environment: {{ ag_ui_env }}
          ╚════════════════════════════════════════╝
  
  roles:
    - role: ag_ui_deployment
      tags: [ag-ui, deployment]
  
  post_tasks:
    - name: Wait for services to be healthy
      ansible.builtin.uri:
        url: "http://{{ ansible_host }}/health"
        status_code: 200
      register: health_check
      until: health_check.status == 200
      retries: 30
      delay: 10
    
    - name: Display deployment success
      ansible.builtin.debug:
        msg: |
          ╔════════════════════════════════════════╗
          ║  Shield AG-UI Deployed Successfully! ✅ ║
          ╠════════════════════════════════════════╣
          ║  Access: https://{{ ansible_host }}/
          ║  Frontend: http://{{ ansible_host }}:3001
          ║  Backend: http://{{ ansible_host }}:8002
          ║  
          ║  Next steps:
          ║  1. Test authentication
          ║  2. Run E2E tests
          ║  3. Validate SLOs
          ╚════════════════════════════════════════╝
```

### Acceptance Criteria

- [ ] Playbook deploys complete stack
- [ ] Pre-flight checks validate target
- [ ] All services start healthy
- [ ] Post-deployment health check passes
- [ ] Rollback on failure
- [ ] Idempotent (can run multiple times)

**Run Playbook**:
```bash
ansible-playbook playbooks/deploy-ag-ui.yml -i inventory/prod.ini --limit hx-dev-server
```

---

## T015: Performance Testing & SLO Validation

**Phase**: 3.5 Polish  
**Parallel**: No (requires deployed system)  
**Estimated Effort**: 4 hours  
**Prerequisites**: T014 (Deployed system)

### Description

Perform load testing to validate performance SLOs: P95 ≤ 800ms @ 10 users, ≤ 1200ms @ 50 users, error rate < 0.5%.

### Key Deliverables

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class AGUIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before running tasks"""
        self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
    
    @task(5)
    def view_dashboard(self):
        """View dashboard (most common)"""
        self.client.get("/dashboard")
    
    @task(3)
    def execute_query(self):
        """Execute knowledge query"""
        self.client.post("/api/query", json={
            "query": "What is Python?",
            "mode": "hybrid"
        })
    
    @task(2)
    def crawl_web(self):
        """Initiate web crawl"""
        self.client.post("/api/crawl", json={
            "url": "https://example.com",
            "max_pages": 10
        })
    
    @task(1)
    def view_graph(self):
        """View knowledge graph"""
        self.client.get("/api/graph")
```

**Test Scenarios**:
1. **Baseline**: 10 concurrent users, 5 minutes
2. **Burst**: Ramp from 10 to 50 users over 2 minutes
3. **Sustained**: 20 concurrent users, 10 minutes
4. **Stress**: Ramp to 100 users to find breaking point

### Acceptance Criteria

- [ ] P95 latency ≤ 800ms @ 10 users
- [ ] P95 latency ≤ 1200ms @ 50 users
- [ ] Error rate < 0.5%
- [ ] Event stream latency < 100ms
- [ ] Page load time < 2 seconds
- [ ] No memory leaks during 10-minute test
- [ ] System recovers after stress test

**Run Tests**:
```bash
# Baseline test (10 users)
locust -f tests/performance/locustfile.py --host=https://192.168.10.12 \
  --users 10 --spawn-rate 2 --run-time 5m --headless

# Burst test (50 users)
locust -f tests/performance/locustfile.py --host=https://192.168.10.12 \
  --users 50 --spawn-rate 5 --run-time 10m --headless

# Generate report
locust -f tests/performance/locustfile.py --host=https://192.168.10.12 \
  --users 10 --spawn-rate 2 --run-time 5m --html=report.html
```

---

## T016: Documentation & Runbook

**Phase**: 3.5 Polish  
**Parallel**: [P] Can run with T015  
**Estimated Effort**: 2 hours  
**Prerequisites**: T014 (Deployed system)

### Description

Create comprehensive user documentation and operational runbook for Shield AG-UI.

### Key Deliverables

**1. User Guide** (`docs/USER-GUIDE.md`):
- Getting started
- Authentication & registration
- Web crawling workflow
- Document upload
- Knowledge graph exploration
- Query interface
- Job tracking
- Keyboard shortcuts
- Troubleshooting

**2. Operational Runbook** (`docs/RUNBOOK.md`):
- Deployment procedures
- Service management (start/stop/restart)
- Health checks
- Log locations
- Common issues & fixes
- Performance monitoring
- Backup & restore
- Disaster recovery
- Security best practices
- Upgrade procedures

**3. API Documentation** (`docs/API.md`):
- Authentication endpoints
- Tool execution endpoints
- Job management endpoints
- Admin endpoints
- SSE event streaming
- Error codes
- Rate limits
- Examples (curl, Python, JavaScript)

**4. VPAT (Accessibility)** (`docs/VPAT.md`):
- WCAG 2.2 AA compliance statement
- Keyboard navigation guide
- Screen reader compatibility
- Known accessibility issues
- Remediation timeline

### Acceptance Criteria

- [ ] User guide complete (20+ pages)
- [ ] Runbook complete (15+ pages)
- [ ] API documentation complete
- [ ] VPAT drafted
- [ ] All code examples tested
- [ ] Screenshots included
- [ ] Table of contents & search

---

## Summary

### Total Remaining Effort

| Phase | Tasks | Hours | Status |
|-------|-------|-------|--------|
| **Tests** | T006-T009 | 12h | [P] Can parallelize |
| **Auth & RBAC** | T010-T011 | 5h | Sequential |
| **Polish** | T012-T013 | 5h | [P] Can parallelize |
| **Deploy** | T014 | 2h | Sequential |
| **Validate** | T015-T016 | 6h | T016 parallel |
| **Total** | **11 tasks** | **30h** | ~4 days with 3 devs |

### Dependencies

```
T006-T009 (Tests - parallel)
    ↓
T010 (Auth Service)
    ↓
T011 (RBAC Service)
    ↓
T012 + T013 (parallel: Audit Logging, Chunked Upload)
    ↓
T014 (Ansible Playbook)
    ↓
T015 (Performance Testing) + T016 (parallel: Documentation)
```

### Execution Strategy

**Day 1**: Launch T006-T009 in parallel (12h → 3-4h with 4 devs)  
**Day 2**: T010 + T011 sequentially (5h)  
**Day 3**: T012 + T013 in parallel (5h → 3h with 2 devs)  
**Day 3-4**: T014 deployment (2h)  
**Day 4**: T015 + T016 in parallel (6h → 4h with 2 devs)

**Total**: 4 business days with proper parallelization

---

**Next Step**: Create individual task files from this document as needed, or use this as a comprehensive guide for execution.

**Status**: ✅ Ready for Implementation  
**Last Updated**: October 11, 2025

