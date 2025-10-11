# CI/CD Workflow Sequence Diagrams

**Date**: October 11, 2025  
**Version**: 1.0

This document contains sequence diagrams for all CI/CD workflows in the repository.

---

## Table of Contents

1. [AI Fix CodeRabbit Issues Workflow](#ai-fix-coderabbit-issues-workflow)
2. [Type Check Workflow](#type-check-workflow)
3. [Claude Code Review Workflow](#claude-code-review-workflow)
4. [Claude Code Interactive Workflow](#claude-code-interactive-workflow)

---

## AI Fix CodeRabbit Issues Workflow

**Purpose**: Automated issue remediation triggered by Linear issues labeled as critical/high severity

**File**: `.github/workflows/ai-fix-coderabbit-issues.yml`

### Full Workflow Sequence

```mermaid
sequenceDiagram
    autonumber
    
    actor User
    participant Linear
    participant GitHub as GitHub Actions
    participant Repo as Repository
    participant Python as Python Setup
    participant Scripts as Shell Scripts
    participant Tests as Test Suite
    participant Slack
    participant PR as Pull Request
    
    %% Trigger Phase
    User->>Linear: Create/Label Issue (critical/high)
    Linear->>GitHub: Webhook/Dispatch Event
    
    Note over GitHub: Circuit Breaker Check<br/>(skip if ai-fix branch)
    
    alt Severity Check Failed
        GitHub->>GitHub: Skip Workflow
    else Severity Critical/High
        GitHub->>Slack: 🤖 Workflow Started
        
        %% Setup Phase
        GitHub->>Repo: Checkout (fetch-depth: 0)
        GitHub->>Python: Setup Python 3.12
        Python->>Python: Cache pip (requirements-dev.txt)
        GitHub->>Python: Install dependencies
        Python->>Python: Verify pytest, mypy, ansible-lint
        GitHub->>Repo: Configure git (actions bot)
        
        %% Fetch Linear Issue
        GitHub->>Linear: GraphQL: Fetch Issue Details
        Linear-->>GitHub: Issue Data (ID, Title, Labels, Description)
        
        %% AI Tool Selection
        GitHub->>GitHub: Determine AI Tool
        
        alt Labels: security|critical
            Note over GitHub: Tool: claude-code<br/>Deep reasoning required
        else Labels: quality|refactor
            Note over GitHub: Tool: cursor<br/>Fast iteration
        else Labels: type-hints|mypy
            Note over GitHub: Tool: auto-fix<br/>Rules-based
        else Labels: formatting|linting
            Note over GitHub: Tool: pre-commit<br/>Automated tool
        else Default
            Note over GitHub: Tool: claude-code<br/>Safe default
        end
        
        %% Branch Creation
        GitHub->>Repo: Create Fix Branch
        Note over Repo: Branch: {IDENTIFIER}-ai-fix
        
        %% Apply Fix
        alt Tool: auto-fix
            GitHub->>Scripts: Run mypy auto-fix
            Scripts-->>GitHub: Type hints added
        else Tool: pre-commit
            GitHub->>Scripts: Run pre-commit hooks
            Scripts-->>GitHub: Formatting applied
        else Tool: claude-code
            GitHub->>GitHub: Create PR Template
            Note over GitHub: Manual intervention required<br/>(Phase 2B limitation)
        end
        
        %% Validation Phase
        par Run Tests in Parallel
            GitHub->>Tests: pytest (continue-on-error)
            Tests-->>GitHub: Test Results
        and Type Checking
            GitHub->>Tests: mypy (continue-on-error)
            Tests-->>GitHub: Type Check Results
        and Linting
            GitHub->>Tests: ansible-lint (continue-on-error)
            Tests-->>GitHub: Lint Results
        end
        
        %% Commit Phase
        alt Changes Detected
            GitHub->>Repo: git add -A
            GitHub->>Repo: git commit (with metadata)
            GitHub->>Repo: git push origin branch
            
            %% Create PR
            GitHub->>GitHub: Build PR Body (printf)
            Note over GitHub: PR Body includes:<br/>- Issue details<br/>- AI tool used<br/>- Test results<br/>- Checklist
            
            GitHub->>PR: gh pr create
            PR-->>GitHub: PR URL
            
            %% Notifications
            GitHub->>Slack: ✅ PR Created (if webhook configured)
            GitHub->>Linear: Comment with PR Link
            Linear-->>User: Notification
            
            GitHub->>GitHub: Write Step Summary
            
        else No Changes
            GitHub->>Slack: ⚠️ No Changes Generated
            Note over GitHub: Workflow ends without PR
        end
        
    end
    
    %% Error Handling
    alt Workflow Failed
        GitHub->>Slack: ❌ Workflow Failed
        GitHub->>GitHub: Write Error Summary
    end
    
    Note over User,PR: Phase 2B: Semi-Automated<br/>Phase 3: Full automation with webhooks
```

### Key Decision Points

```mermaid
flowchart TD
    Start([Workflow Triggered]) --> CircuitBreaker{Circuit Breaker<br/>Check}
    CircuitBreaker -->|ai-fix branch| Skip([Skip Workflow])
    CircuitBreaker -->|normal branch| Severity{Severity<br/>Check}
    
    Severity -->|low/medium| Skip
    Severity -->|critical/high| Fetch[Fetch Linear Issue]
    
    Fetch --> Route{Route by<br/>Labels}
    
    Route -->|security/critical| Claude[Claude Code<br/>Deep Reasoning]
    Route -->|quality/refactor| Cursor[Cursor<br/>Fast Iteration]
    Route -->|type-hints/mypy| Auto[Auto-Fix<br/>Rules-Based]
    Route -->|formatting/linting| PreCommit[Pre-commit<br/>Automated]
    Route -->|default| Claude
    
    Claude --> Apply[Apply Fix]
    Cursor --> Apply
    Auto --> Apply
    PreCommit --> Apply
    
    Apply --> Validate[Run Tests<br/>Type Check<br/>Lint]
    
    Validate --> Changes{Changes<br/>Detected?}
    
    Changes -->|Yes| Commit[Commit & Push]
    Changes -->|No| NoChange[Notify: No Changes]
    
    Commit --> CreatePR[Create PR]
    CreatePR --> Notify[Notify Slack & Linear]
    
    Notify --> End([Workflow Complete])
    NoChange --> End
    Skip --> End
    
    style Claude fill:#e1f5ff
    style Cursor fill:#fff4e1
    style Auto fill:#e8f5e9
    style PreCommit fill:#f3e5f5
```

### AI Tool Selection Logic

```mermaid
graph LR
    Labels[Issue Labels] --> Security{Contains<br/>security OR<br/>coderabbit-critical?}
    Labels --> Quality{Contains<br/>coderabbit-quality OR<br/>refactor?}
    Labels --> TypeHints{Contains<br/>type-hints OR<br/>mypy?}
    Labels --> Format{Contains<br/>formatting OR<br/>linting?}
    
    Security -->|Yes| ClaudeCode[Claude Code]
    Security -->|No| Quality
    
    Quality -->|Yes| Cursor[Cursor]
    Quality -->|No| TypeHints
    
    TypeHints -->|Yes| AutoFix[Auto-Fix]
    TypeHints -->|No| Format
    
    Format -->|Yes| PreCommit[Pre-commit]
    Format -->|No| Default[Claude Code<br/>Default]
    
    style ClaudeCode fill:#ff6b6b
    style Cursor fill:#4ecdc4
    style AutoFix fill:#95e1d3
    style PreCommit fill:#f38181
    style Default fill:#aa96da
```

---

## Type Check Workflow

**Purpose**: Validate Python type hints on push/PR

**File**: `.github/workflows/type-check.yml`

```mermaid
sequenceDiagram
    autonumber
    
    actor Developer
    participant GitHub as GitHub Actions
    participant Repo as Repository
    participant Python as Python 3.12
    participant Mypy as Mypy Type Checker
    participant Templates as Jinja2 Templates
    participant Artifacts as Artifacts Storage
    
    Developer->>Repo: Push to main/feature/**
    Note over Developer,Repo: Triggers on:<br/>- *.py files<br/>- *.py.j2 files<br/>- mypy.ini<br/>- requirements-dev.txt
    
    Repo->>GitHub: Trigger Workflow
    
    GitHub->>Repo: Checkout code
    GitHub->>Python: Setup Python 3.12
    Python->>Python: Cache pip (requirements-dev.txt)
    GitHub->>Python: pip install -r requirements-dev.txt
    
    GitHub->>GitHub: Validate mypy.ini exists
    
    alt mypy.ini not found
        GitHub->>GitHub: ❌ Exit with error
    else mypy.ini found
        GitHub->>GitHub: ✅ Configuration valid
        
        GitHub->>Repo: Find Python files (exclude tech_kb, .venv)
        
        alt Python files exist
            GitHub->>Mypy: mypy . --config-file=mypy.ini
            Mypy-->>GitHub: Type check results (continue-on-error)
        else No Python files
            GitHub->>GitHub: ⚠️ No files to check (templates only)
        end
        
        GitHub->>Templates: Find *.py.j2 templates
        
        loop For each template
            GitHub->>Templates: Check for type hint patterns
            Templates-->>GitHub: Has typing imports / annotations?
            
            alt Has type hints
                GitHub->>GitHub: ✅ Template validated
            else No type hints
                GitHub->>GitHub: ⚠️ May be missing hints
            end
        end
        
        GitHub->>GitHub: Calculate coverage %
        
        alt Coverage >= 80%
            GitHub->>GitHub: ✅ Meets target
        else Coverage < 80%
            GitHub->>GitHub: ⚠️ Below target (warning only)
        end
        
        GitHub->>GitHub: Generate GITHUB_STEP_SUMMARY
        GitHub->>Artifacts: Upload .mypy_cache/
        
        Note over GitHub: Full validation happens<br/>on deployed servers
    end
    
    GitHub-->>Developer: Workflow Complete
```

---

## Claude Code Review Workflow

**Purpose**: Automated PR review using Claude AI

**File**: `.github/workflows/claude-code-review.yml`

```mermaid
sequenceDiagram
    autonumber
    
    actor Contributor
    participant PR as Pull Request
    participant GitHub as GitHub Actions
    participant Repo as Repository
    participant Claude as Claude Code AI
    participant GH_CLI as GitHub CLI
    
    Contributor->>PR: Open/Update PR
    PR->>GitHub: Trigger (opened, synchronize)
    
    GitHub->>Repo: Checkout (fetch-depth: 1)
    
    GitHub->>Claude: Initialize Claude Code Action
    Note over Claude: OAuth Token: CLAUDE_CODE_OAUTH_TOKEN
    
    Claude->>Repo: Read CLAUDE.md (style guide)
    Claude->>PR: Fetch PR diff
    Claude->>PR: Read PR description
    
    Note over Claude: Review Checklist:<br/>- Code quality & best practices<br/>- Potential bugs<br/>- Performance considerations<br/>- Security concerns<br/>- Test coverage
    
    Claude->>Claude: Analyze Changes
    
    alt Issues Found or Suggestions
        Claude->>GH_CLI: gh pr comment (with review)
        GH_CLI->>PR: Post Review Comment
        PR-->>Contributor: Notification
    else No Issues
        Claude->>GH_CLI: gh pr comment (approval)
        GH_CLI->>PR: Post Approval Comment
        PR-->>Contributor: Notification
    end
    
    GitHub-->>GitHub: Workflow Complete
    
    Note over GitHub,Claude: Allowed Tools:<br/>- gh issue view<br/>- gh search<br/>- gh issue list<br/>- gh pr comment<br/>- gh pr diff<br/>- gh pr view<br/>- gh pr list
```

---

## Claude Code Interactive Workflow

**Purpose**: Interactive Claude Code assistance via @mentions

**File**: `.github/workflows/claude.yml`

```mermaid
sequenceDiagram
    autonumber
    
    actor User
    participant Issue as Issue/PR
    participant GitHub as GitHub Actions
    participant Repo as Repository
    participant Claude as Claude Code AI
    participant CI as CI Results
    
    User->>Issue: Comment/Create with @claude
    Note over User,Issue: Triggers:<br/>- Issue comment<br/>- PR review comment<br/>- PR review<br/>- New issue with @claude
    
    Issue->>GitHub: Event Triggered
    
    GitHub->>GitHub: Check for @claude mention
    
    alt No @claude found
        GitHub->>GitHub: Skip workflow
    else @claude found
        GitHub->>Repo: Checkout (fetch-depth: 1)
        
        GitHub->>Claude: Initialize Claude Code Action
        Note over Claude: OAuth Token: CLAUDE_CODE_OAUTH_TOKEN<br/>Permissions: read contents, PRs, issues, actions
        
        Claude->>Issue: Read user's request
        Claude->>Repo: Access repository context
        
        alt PR Context
            Claude->>CI: Read CI results (if available)
            CI-->>Claude: Test results, linting, etc.
        end
        
        Claude->>Repo: Analyze codebase (as needed)
        Claude->>Claude: Process user request
        
        alt Custom prompt provided
            Claude->>Claude: Execute custom prompt
        else No custom prompt
            Claude->>Claude: Execute user's @claude comment
        end
        
        Claude->>Issue: Respond with analysis/suggestions
        Issue-->>User: Notification
        
        Note over Claude: Can use any bash tools<br/>(gh commands, git, etc.)
    end
    
    GitHub-->>GitHub: Workflow Complete
```

---

## Integration Points

### Secrets Required

| Secret | Used By | Purpose |
|--------|---------|---------|
| `LINEAR_SECRET` | AI Fix Workflow | Fetch Linear issues, post comments |
| `GITHUB_TOKEN` | All Workflows | Repository operations (auto-provided) |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Workflows | Claude AI authentication |
| `SLACK_WEBHOOK_URL` | AI Fix Workflow | Notifications (optional) |

### External Services

```mermaid
graph TB
    GHA[GitHub Actions] -->|GraphQL| Linear[Linear API]
    GHA -->|Webhook| Slack[Slack Notifications]
    GHA -->|OAuth| Claude[Claude Code API]
    GHA -->|REST API| GitHub[GitHub API]
    
    Linear -->|Issue Data| GHA
    GHA -->|PR/Comment| GitHub
    GHA -->|Notifications| Slack
    Claude -->|Code Review| GHA
    
    style GHA fill:#2088ff
    style Linear fill:#5e6ad2
    style Slack fill:#4a154b
    style Claude fill:#d97706
    style GitHub fill:#24292e
```

---

## Workflow Triggers Summary

| Workflow | Trigger Type | Conditions |
|----------|-------------|------------|
| **AI Fix** | `repository_dispatch`, `workflow_dispatch` | Critical/High severity, not ai-fix branch |
| **Type Check** | `push`, `pull_request` | Changes to `*.py`, `*.py.j2`, `mypy.ini`, `requirements-dev.txt` |
| **Claude Review** | `pull_request` | PR opened or synchronized |
| **Claude Interactive** | `issue_comment`, `pull_request_review_comment`, `issues` | Contains `@claude` mention |

---

## Phase Evolution

### Current: Phase 2B (Semi-Automated)

```mermaid
graph LR
    A[Manual Issue Creation] --> B[Workflow Dispatch]
    B --> C[AI Analysis]
    C --> D[Create PR]
    D --> E[Manual Review]
    E --> F[Manual Merge]
    
    style B fill:#fff4e1
    style E fill:#fff4e1
```

### Future: Phase 3 (Full Automation)

```mermaid
graph LR
    A[CodeRabbit Detects Issue] --> B[Linear Webhook]
    B --> C[Auto Workflow Trigger]
    C --> D[AI Auto-Fix]
    D --> E[Auto PR Creation]
    E --> F[Auto Tests]
    F --> G{Tests Pass?}
    G -->|Yes| H[Auto Merge]
    G -->|No| I[Human Review]
    H --> J[Auto Update Linear]
    I --> J
    
    style A fill:#e8f5e9
    style H fill:#e8f5e9
    style C fill:#e1f5ff
    style D fill:#e1f5ff
```

---

## Error Handling Flow

```mermaid
stateDiagram-v2
    [*] --> WorkflowStart
    
    WorkflowStart --> CircuitBreaker
    CircuitBreaker --> Skipped: ai-fix branch
    CircuitBreaker --> SeverityCheck: Normal branch
    
    SeverityCheck --> Skipped: Low/Medium
    SeverityCheck --> FetchIssue: Critical/High
    
    FetchIssue --> APIError: Linear API fails
    FetchIssue --> ApplyFix: Success
    
    ApplyFix --> TestFailed: Tests fail
    ApplyFix --> NoChanges: No modifications
    ApplyFix --> CreatePR: Tests pass
    
    TestFailed --> CreatePR: Continue (non-blocking)
    NoChanges --> NotifyNoChanges
    
    CreatePR --> PRCreated
    PRCreated --> NotifySuccess
    
    APIError --> NotifyFailure
    NotifyFailure --> [*]
    NotifySuccess --> [*]
    NotifyNoChanges --> [*]
    Skipped --> [*]
    
    note right of TestFailed
        Tests are continue-on-error
        PR is created with test status
    end note
```

---

## Performance Metrics

| Workflow | Typical Duration | Timeout | Concurrency |
|----------|-----------------|---------|-------------|
| AI Fix | 15-25 minutes | 30 minutes | No limit |
| Type Check | 2-5 minutes | None (default 360 min) | No limit |
| Claude Review | 3-8 minutes | None (default 360 min) | No limit |
| Claude Interactive | 2-10 minutes | None (default 360 min) | No limit |

---

## Best Practices Implemented

1. ✅ **Circuit Breaker**: Prevents infinite loops on ai-fix branches
2. ✅ **Explicit Permissions**: Least privilege for each workflow
3. ✅ **Fail-Safe Testing**: Tests continue-on-error, status reported in PR
4. ✅ **Shallow Clones**: fetch-depth: 1 where possible (except AI fix needs full history)
5. ✅ **Pip Caching**: Speeds up Python setup with requirements-dev.txt cache
6. ✅ **Error Notifications**: Slack notifications for all failure scenarios
7. ✅ **Step Summaries**: GitHub Actions summaries for quick overview

---

**Last Updated**: October 11, 2025  
**Maintained By**: DevOps Team  
**Review Frequency**: After major workflow changes

