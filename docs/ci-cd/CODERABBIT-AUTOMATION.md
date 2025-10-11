# CodeRabbit Automation Workflow
## AI-Assisted Issue Remediation

**Status**: Phase 2A Implementation (Interim Solution)
**Created**: October 11, 2025
**Owner**: DevOps Team
**Integration**: CodeRabbit → Linear → AI Tools

---

## 📋 Overview

This document describes the automated workflow for managing and remediating CodeRabbit findings using Linear issue tracking and AI-assisted remediation tools.

**Problem Solved**: Manual copy/paste of CodeRabbit findings was creating bottlenecks and delaying development. This automation eliminates manual tracking and accelerates issue resolution.

---

## 🏗️ Architecture

```
┌─────────────────┐
│  CodeRabbit PR  │
│     Review      │
└────────┬────────┘
         │ (auto-detect findings)
         ▼
┌─────────────────────────────────┐
│  .coderabbit.yaml Configuration │
│  - Severity classification      │
│  - Auto-test generation         │
│  - Ansible-specific rules       │
└────────┬────────────────────────┘
         │
         ├─── Critical/High ──────▶ ┌──────────────────┐
         │                          │  Linear Issue    │
         │                          │  (Auto-created)  │
         │                          └────────┬─────────┘
         │                                   │
         │                                   ▼
         │                          ┌──────────────────┐
         │                          │  AI Remediation  │
         │                          │  (Claude/Cursor) │
         │                          └────────┬─────────┘
         │                                   │
         │                                   ▼
         │                          ┌──────────────────┐
         │                          │   Fix Branch +   │
         │                          │   Create PR      │
         │                          └──────────────────┘
         │
         └─── Medium/Low ────────▶  Batch into weekly cleanup

```

---

## 🚀 Quick Start

### Step 1: Enable Linear Integration

1. Go to CodeRabbit settings → Integrations
2. Click "Enable Linear Integration"
3. Authorize Linear workspace access
4. CodeRabbit will now validate issues and auto-create new ones

### Step 2: Configure Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxx"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxx"
```

### Step 3: Create Linear Labels

Create the following labels in your Linear workspace:

| Label | Description | Color |
|-------|-------------|-------|
| `coderabbit-finding` | Auto-created by CodeRabbit | 🔴 Red |
| `coderabbit-critical` | Critical security/breaking issues | 🔴 Red |
| `coderabbit-quality` | Code quality improvements | 🟡 Yellow |
| `coderabbit-nitpick` | Minor formatting/style issues | 🔵 Blue |
| `auto-generated` | Created by automation | 🟣 Purple |
| `ai-generated` | Fixed by AI tool | 🟢 Green |

### Step 4: Test the Workflow

```bash
# Create a test PR with a known issue
git checkout -b test-coderabbit-automation
echo "def test_function():" >> tests/test_sample.py
echo "    pass" >> tests/test_sample.py
git add tests/test_sample.py
git commit -m "test: add sample function without type hints"
git push origin test-coderabbit-automation

# Open PR on GitHub
gh pr create --title "Test CodeRabbit Automation" --body "Testing auto-issue creation"

# Watch for:
# 1. CodeRabbit review comment
# 2. Auto-generated Linear issue (if critical/high)
# 3. Auto-generated unit tests (if applicable)
```

---

## 🔧 Usage

### Manual AI Remediation (Current - Phase 2A)

When a Linear issue is created from CodeRabbit:

```bash
# Fix a specific Linear issue
./scripts/fix-linear-issue.sh DEV-123

# The script will:
# 1. Fetch issue details from Linear
# 2. Determine appropriate AI tool
# 3. Create fix branch
# 4. Route to AI for remediation
# 5. Commit changes and create PR
```

### Issue Routing Rules

The script automatically routes issues based on labels and severity:

| Issue Type | AI Tool | Rationale |
|-----------|---------|-----------|
| **Critical Security** (`coderabbit-critical`, `security`) | Claude Code (Sonnet) | Complex reasoning, security context |
| **Code Quality** (`coderabbit-quality`, `refactor`) | Cursor (fast model) | Quick refactors, pattern fixes |
| **Type Hints** (`type-hints`, `mypy`) | Automated script | Rules-based, no AI needed |
| **Test Coverage** (`tests`, `coverage`) | Claude Code | Business logic understanding |
| **Formatting** (`formatting`, `linting`) | Pre-commit hooks | Fully automated |
| **Documentation** (`documentation`) | Claude Code (Haiku) | Cost-effective docs generation |

---

## 📊 Severity Classification

CodeRabbit findings are automatically categorized:

### Critical (Auto-create Linear issue + Immediate action)
- 🔴 Security vulnerabilities
- 🔴 Breaking changes
- 🔴 Data loss risk
- 🔴 Authentication bypass
- 🔴 Plain-text secrets

### High (Auto-create Linear issue + Weekly sprint)
- 🟡 Performance issues
- 🟡 Code smells (high complexity)
- 🟡 Missing error handling
- 🟡 Implicit Optional types

### Medium (Batch into weekly cleanup issue)
- 🔵 Code duplication
- 🔵 Missing docstrings
- 🔵 Long functions (>50 lines)
- 🔵 Magic numbers

### Low (Ignore for .md, flag for .py/.yml)
- ⚪ Formatting issues
- ⚪ Naming conventions
- ⚪ Comment style

---

## 🎯 Project-Specific Rules

### Ansible Best Practices (enforced)

Per `docs/ANSIBLE-BEST-PRACTICES.md`:

1. **FQCN Required** (Critical)
   ```yaml
   # ❌ BAD - CodeRabbit will flag as critical
   - name: Install package
     apt:
       name: nginx

   # ✅ GOOD
   - name: Install package
     ansible.builtin.apt:
       name: nginx
   ```

2. **changed_when Required** (High)
   ```yaml
   # ❌ BAD - CodeRabbit will flag as high
   - name: Check status
     ansible.builtin.shell: systemctl status nginx

   # ✅ GOOD
   - name: Check status
     ansible.builtin.shell: systemctl status nginx
     changed_when: false
   ```

3. **Explicit File Permissions** (High)
   ```yaml
   # ❌ BAD - CodeRabbit will flag as high
   - name: Create config
     ansible.builtin.copy:
       src: config.yml
       dest: /etc/config.yml

   # ✅ GOOD
   - name: Create config
     ansible.builtin.copy:
       src: config.yml
       dest: /etc/config.yml
       mode: '0644'
   ```

### Python Type Hints (enforced)

Per Phase 2 Sprint 2.1 (Type Hints Migration):

```python
# ❌ BAD - CodeRabbit will flag as medium
def process_data(data, optional_param=None):
    return data

# ✅ GOOD
from typing import Optional, Any

def process_data(data: dict[str, Any], optional_param: Optional[str] = None) -> dict[str, Any]:
    return data
```

---

## 🔄 Automated Features

### 1. Auto-Generated Unit Tests

CodeRabbit can automatically generate pytest tests:

**Configuration** (`.coderabbit.yaml`):
```yaml
reviews:
  auto_generate_tests:
    enabled: true
    test_framework: "pytest"
    auto_commit: true
    coverage_target: 80
```

**When triggered**:
- CodeRabbit detects new functions without tests
- Generates pytest test cases
- Auto-commits to current PR branch
- Achieves 80%+ coverage target (per TASK-032)

**Example**: If you add `def calculate_total(items):`, CodeRabbit will generate:
```python
def test_calculate_total_with_empty_list():
    assert calculate_total([]) == 0

def test_calculate_total_with_single_item():
    assert calculate_total([5]) == 5

def test_calculate_total_with_multiple_items():
    assert calculate_total([1, 2, 3]) == 6
```

### 2. Auto-Created Linear Issues

For **critical** and **high** severity findings:

**Trigger**: CodeRabbit completes review and flags critical/high issue
**Action**: Linear issue automatically created
**Template**:
```
Title: [CodeRabbit] {finding_type}: {file_name}

Description:
CodeRabbit finding from PR #{pr_number}

**File**: {file_path}:{line_number}
**Severity**: {severity}
**Category**: {category}

**Issue**:
{description}

**Recommended Fix**:
{recommendation}

**Related PR**: #{pr_number}

Labels: coderabbit-finding, coderabbit-{severity}, auto-generated
Priority: {mapped_priority}
```

### 3. Path-Based Review Filtering

**Critical Paths** (thorough review):
- `roles/*/tasks/*.yml` - Ansible tasks
- `roles/*/templates/*.j2` - Jinja2 templates
- `playbooks/*.yml` - Playbooks
- `site.yml` - Main orchestrator

**Documentation Paths** (lighter review, skip nitpicks):
- `docs/**/*.md`
- `README.md`

**Test Paths** (focus on coverage):
- `tests/**/*.py`

**Ignored Paths** (performance):
- `tech_kb/**` - Large knowledge base (33 repos, 67K+ files)
- `**/__pycache__/**`
- `.pytest_cache/**`

---

## 🛠️ Scripts Reference

### fix-linear-issue.sh

**Purpose**: Route Linear issues to appropriate AI remediation tool
**Location**: `scripts/fix-linear-issue.sh`
**Usage**:
```bash
./scripts/fix-linear-issue.sh <linear-issue-id>

# Examples:
./scripts/fix-linear-issue.sh DEV-123    # Fix issue DEV-123
./scripts/fix-linear-issue.sh DEV-124    # Fix issue DEV-124
```

**Workflow**:
1. Fetch Linear issue via GraphQL API
2. Parse severity and labels
3. Determine AI tool (Claude Code, Cursor, or auto-fix)
4. Create fix branch (`fix/dev-123`)
5. Apply AI remediation
6. Commit changes with conventional commit message
7. Create PR with issue link

**Environment Requirements**:
- `LINEAR_API_KEY` - Linear API token
- `GITHUB_TOKEN` - GitHub personal access token
- `jq` - JSON parser (install: `sudo apt install jq`)
- `gh` - GitHub CLI (install: `sudo apt install gh`)

---

## 📈 Metrics and Monitoring

### Key Metrics (to be tracked in Phase 3)

| Metric | Target | Current |
|--------|--------|---------|
| **Auto-remediated issues** | 70%+ | - |
| **Time to fix (critical)** | < 4 hours | - |
| **Time to fix (high)** | < 2 days | - |
| **CodeRabbit coverage** | 95%+ PRs | - |
| **False positive rate** | < 5% | - |
| **AI fix success rate** | > 80% | - |

**Dashboard** (Phase 3 - TASK-047-050):
- Grafana dashboard showing issue creation/resolution rates
- Alert on high false positive rate
- Track AI tool performance (Claude vs Cursor vs Auto-fix)

---

## 🔮 Future Enhancements (Phase 2B & 3)

### Phase 2B: Semi-Automated (TASK-035)

**GitHub Action: AI Remediation Trigger**
```yaml
# .github/workflows/ai-fix-issues.yml
name: AI Issue Remediation
on:
  issues:
    types: [labeled]
jobs:
  ai-fix:
    if: contains(github.event.label.name, 'coderabbit-')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Trigger AI Fix
        run: ./scripts/fix-linear-issue.sh ${{ github.event.issue.id }}

      - name: Run Tests
        run: pytest tests/

      - name: Create PR if tests pass
        if: success()
        run: gh pr create --title "Fix ${{ github.event.issue.title }}" --body "Auto-fix"
```

### Phase 3: Full Automation (Sprint 3.2)

**Webhook Pipeline**:
```
CodeRabbit Webhook
  ↓
Cloud Function (AWS Lambda/Google Cloud Run)
  ↓
Linear GraphQL API (auto-create issue)
  ↓
AI Remediation Service (Claude Code API)
  ↓
GitHub API (auto-create PR)
  ↓
CodeRabbit Re-review
  ↓
Auto-merge (if approved)
```

**Knowledge Base Integration**:
- Store all CodeRabbit findings in Qdrant vector database
- Use LightRAG to query: "Similar issues to current finding?"
- AI learns from past fixes and suggests solutions
- Builds institutional knowledge over time

---

## ❓ Troubleshooting

### Issue: Linear API Key Not Working

**Symptom**: `Error: LINEAR_API_KEY environment variable not set`

**Solution**:
```bash
# Generate new API key from Linear settings
# https://linear.app/settings/api

# Add to environment
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"

# Or add to ~/.bashrc permanently
echo 'export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: CodeRabbit Not Creating Linear Issues

**Symptom**: CodeRabbit reviews PR but doesn't create Linear issues

**Check**:
1. ✅ Linear integration enabled in CodeRabbit settings?
2. ✅ `.coderabbit.yaml` committed to repository root?
3. ✅ Finding severity is critical or high?
4. ✅ Linear labels exist (`coderabbit-finding`, `auto-generated`)?

**Solution**:
```bash
# Verify .coderabbit.yaml is in repo root
ls -la .coderabbit.yaml

# Check CodeRabbit settings
# Visit: https://app.coderabbit.ai/settings/integrations

# Manually test Linear API
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name } }"}'
```

### Issue: AI Remediation Script Fails

**Symptom**: `./fix-linear-issue.sh` exits with error

**Common Causes**:
1. Missing dependencies (`jq`, `gh` CLI)
2. Not in git repository
3. No issue found in Linear

**Solution**:
```bash
# Install dependencies
sudo apt install jq
sudo apt install gh

# Authenticate GitHub CLI
gh auth login

# Test with verbose output
bash -x ./scripts/fix-linear-issue.sh DEV-123
```

---

## 📚 References

- **CodeRabbit Documentation**: https://docs.coderabbit.ai/
- **Linear API Reference**: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- **GitHub CLI**: https://cli.github.com/manual/
- **Ansible Best Practices**: `docs/ANSIBLE-BEST-PRACTICES.md`
- **Type Checking Guide**: `docs/TYPE-CHECKING-GUIDE.md`
- **Task Tracker**: `docs/Delivery-Enhancements/TASK-TRACKER.md`

---

## 👥 Support

**Questions or Issues**:
- Review CodeRabbit findings in PR comments
- Check Linear issues with `coderabbit-finding` label
- Run remediation script with `-h` flag for help
- Escalate to Phase 3 (full automation) if bottleneck persists

**Feedback**:
- Adjust severity thresholds in `.coderabbit.yaml`
- Update routing rules in `fix-linear-issue.sh`
- Suggest new custom rules for project-specific patterns

---

**Last Updated**: October 11, 2025
**Version**: 1.0 (Phase 2A - Interim Solution)
**Next Review**: Phase 3 Planning (Monitoring & Alerting)
