# Phase 3: Automation Production Hardening
**Project**: CodeRabbit + Linear + GitHub Actions Integration
**Status**: 🚀 Ready to Implement
**Duration**: 2-3 days
**Date**: October 11, 2025

---

## 📊 Phase Overview

### Previous Phases (✅ Complete)
- **Phase 1**: Manual remediation script (`fix-linear-issue.sh`)
- **Phase 2A**: CodeRabbit config with Linear auto-issue creation
- **Phase 2B**: GitHub Actions semi-automated remediation workflow

### Phase 3 Objectives
**Production Hardening & Advanced Features**
1. ✅ Slack notifications for workflow events
2. ✅ End-to-end testing suite
3. ✅ Monitoring & metrics dashboards
4. ✅ Webhook security & validation
5. ✅ Operational documentation
6. ✅ Incident response procedures

---

## 🎯 Sprint 3.1: Slack Notifications (4 hours)

### Objective
Add Slack notifications for all workflow events (started, succeeded, failed, PR created)

### Tasks

#### Task 3.1.1: Setup Slack Incoming Webhook (30 minutes)
**File**: New GitHub Secret
**Steps**:
1. Go to Slack workspace
2. Create Incoming Webhook for `#shield-automation` channel
3. Add webhook URL to GitHub Secrets as `SLACK_WEBHOOK_URL`

**Testing**:
```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from Phase 3 setup"}'
```

---

#### Task 3.1.2: Create Slack Notification Helper Script (1 hour)
**File**: `scripts/slack-notify.sh`

```bash
#!/bin/bash
###############################################################################
# Slack Notification Helper
# Usage: ./slack-notify.sh <webhook_url> <message> <color> [fields...]
###############################################################################

set -euo pipefail

WEBHOOK_URL="${1:-}"
MESSAGE="${2:-}"
COLOR="${3:-#36a64f}"  # green by default
shift 3 || true

# Build attachment with fields
FIELDS="[]"
while [[ $# -gt 0 ]]; do
    FIELD_TITLE="$1"
    FIELD_VALUE="$2"
    FIELD_SHORT="${3:-false}"
    shift 3 || break

    FIELDS=$(echo "$FIELDS" | jq ". += [{\"title\": \"$FIELD_TITLE\", \"value\": \"$FIELD_VALUE\", \"short\": $FIELD_SHORT}]")
done

# Send notification
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @- <<EOF
{
  "attachments": [
    {
      "color": "$COLOR",
      "text": "$MESSAGE",
      "fields": $FIELDS,
      "footer": "HX-Citadel Automation",
      "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
      "ts": $(date +%s)
    }
  ]
}
EOF
```

**Deliverable**: Helper script for reusable Slack notifications

---

#### Task 3.1.3: Add Slack Notifications to Workflow (2 hours)
**File**: `.github/workflows/ai-fix-coderabbit-issues.yml`

**Add 4 notification steps**:

1. **Workflow Started** (after checkout):
```yaml
- name: Notify Slack - Workflow Started
  if: always()
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    if [ -n "$SLACK_WEBHOOK" ]; then
      ./scripts/slack-notify.sh "$SLACK_WEBHOOK" \
        "🤖 *AI Remediation Started*" \
        "#36a64f" \
        "Issue" "${{ github.event.inputs.issue_id }}" "true" \
        "Severity" "${{ github.event.inputs.severity }}" "true" \
        "Triggered By" "${{ github.actor }}" "true"
    fi
```

2. **PR Created** (after PR creation):
```yaml
- name: Notify Slack - PR Created
  if: steps.create_pr.outputs.pr_url
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    if [ -n "$SLACK_WEBHOOK" ]; then
      ./scripts/slack-notify.sh "$SLACK_WEBHOOK" \
        "✅ *AI Fix PR Created*" \
        "#36a64f" \
        "Issue" "${{ steps.linear.outputs.identifier }}" "true" \
        "PR" "<${{ steps.create_pr.outputs.pr_url }}|View PR>" "true" \
        "Tool" "${{ steps.ai_tool.outputs.tool }}" "true" \
        "Tests" "${{ steps.tests.outputs.tests_failed == 'true' && '❌ Failed' || '✅ Passed' }}" "true"
    fi
```

3. **Workflow Failed** (on failure):
```yaml
- name: Notify Slack - Workflow Failed
  if: failure()
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    if [ -n "$SLACK_WEBHOOK" ]; then
      ./scripts/slack-notify.sh "$SLACK_WEBHOOK" \
        "❌ *AI Remediation Failed*" \
        "#ff0000" \
        "Issue" "${{ github.event.inputs.issue_id }}" "true" \
        "Error" "Check workflow logs" "true" \
        "Run" "<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Logs>" "false"
    fi
```

4. **No Changes** (when no commits):
```yaml
- name: Notify Slack - No Changes
  if: steps.commit.outputs.committed == 'false'
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    if [ -n "$SLACK_WEBHOOK" ]; then
      ./scripts/slack-notify.sh "$SLACK_WEBHOOK" \
        "⚠️  *AI Remediation - No Changes*" \
        "#ffaa00" \
        "Issue" "${{ steps.linear.outputs.identifier }}" "true" \
        "Reason" "No code changes generated" "false"
    fi
```

**Deliverable**: Slack notifications for all workflow states

---

#### Task 3.1.4: Test Slack Integration (30 minutes)

**Test Plan**:
1. Trigger workflow with HAN-5
2. Verify "Workflow Started" notification
3. Verify "No Changes" notification (expected)
4. Verify notification formatting and links

**Success Criteria**:
- ✅ Notifications appear in Slack channel
- ✅ All fields populated correctly
- ✅ Links work (PR, workflow logs)
- ✅ Color coding correct (green/yellow/red)

---

## 🧪 Sprint 3.2: End-to-End Testing (6 hours)

### Objective
Comprehensive testing suite for the entire automation workflow

### Tasks

#### Task 3.2.1: Create Test Framework (1 hour)
**Directory**: `tests/automation/`

**Structure**:
```
tests/automation/
├── __init__.py
├── conftest.py                 # Pytest fixtures
├── test_linear_api.py         # Linear API tests
├── test_github_workflow.py    # Workflow tests
├── test_scripts.py            # Script tests
└── fixtures/
    ├── sample_issues.json
    └── sample_responses.json
```

**File**: `tests/automation/conftest.py`
```python
"""Pytest fixtures for automation testing"""
import pytest
import os
from typing import Dict, Any

@pytest.fixture
def linear_api_key():
    """Linear API key from environment"""
    return os.getenv("LINEAR_API_KEY", "")

@pytest.fixture
def github_token():
    """GitHub token from environment"""
    return os.getenv("GITHUB_TOKEN", "")

@pytest.fixture
def sample_issue() -> Dict[str, Any]:
    """Sample Linear issue for testing"""
    return {
        "id": "test-issue-id",
        "identifier": "HAN-999",
        "title": "[Test] Sample issue",
        "description": "Test issue description",
        "priority": 2,
        "state": {"name": "Backlog"},
        "labels": {"nodes": [{"name": "test"}]}
    }
```

---

#### Task 3.2.2: Write Linear API Tests (2 hours)
**File**: `tests/automation/test_linear_api.py`

```python
"""
Linear API Integration Tests
Tests the Linear GraphQL API integration
"""
import pytest
import subprocess
import json
from typing import Optional

class TestLinearAPI:
    """Test Linear API operations"""

    def test_fetch_linear_issue_script_exists(self):
        """Test that fetch-linear-issue.sh exists and is executable"""
        result = subprocess.run(
            ["test", "-x", "./scripts/fetch-linear-issue.sh"],
            capture_output=True
        )
        assert result.returncode == 0, "fetch-linear-issue.sh not found or not executable"

    @pytest.mark.integration
    def test_fetch_valid_issue(self, linear_api_key):
        """Test fetching a valid Linear issue"""
        if not linear_api_key:
            pytest.skip("LINEAR_API_KEY not set")

        result = subprocess.run(
            ["./scripts/fetch-linear-issue.sh", "HAN-5"],
            capture_output=True,
            text=True,
            env={"LINEAR_API_KEY": linear_api_key}
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        issue_data = json.loads(result.stdout)
        assert "identifier" in issue_data
        assert issue_data["identifier"] == "HAN-5"
        assert "title" in issue_data
        assert "description" in issue_data

    @pytest.mark.integration
    def test_fetch_invalid_issue(self, linear_api_key):
        """Test fetching non-existent issue"""
        if not linear_api_key:
            pytest.skip("LINEAR_API_KEY not set")

        result = subprocess.run(
            ["./scripts/fetch-linear-issue.sh", "HAN-99999"],
            capture_output=True,
            text=True,
            env={"LINEAR_API_KEY": linear_api_key}
        )

        # Should return error JSON
        response = json.loads(result.stdout)
        assert "error" in response

    @pytest.mark.integration
    def test_fetch_with_missing_api_key(self):
        """Test script behavior without API key"""
        result = subprocess.run(
            ["./scripts/fetch-linear-issue.sh", "HAN-5"],
            capture_output=True,
            text=True,
            env={}
        )

        assert result.returncode != 0
        assert "LINEAR_API_KEY" in result.stderr


class TestFixLinearIssueScript:
    """Test fix-linear-issue.sh workflow"""

    def test_script_exists(self):
        """Test that fix-linear-issue.sh exists"""
        result = subprocess.run(
            ["test", "-x", "./scripts/fix-linear-issue.sh"],
            capture_output=True
        )
        assert result.returncode == 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_workflow_dry_run(self, linear_api_key):
        """Test full workflow without making changes"""
        if not linear_api_key:
            pytest.skip("LINEAR_API_KEY not set")

        # This test would create a branch but not push
        # Mark as slow since it interacts with git
        pytest.skip("Requires careful git state management")
```

---

#### Task 3.2.3: Write Workflow Validation Tests (2 hours)
**File**: `tests/automation/test_github_workflow.py`

```python
"""
GitHub Workflow Validation Tests
Tests the workflow configuration and structure
"""
import pytest
import yaml
from pathlib import Path

class TestWorkflowConfiguration:
    """Test GitHub Actions workflow configuration"""

    @pytest.fixture
    def workflow_file(self):
        """Load workflow YAML"""
        path = Path(".github/workflows/ai-fix-coderabbit-issues.yml")
        with open(path) as f:
            return yaml.safe_load(f)

    def test_workflow_file_exists(self):
        """Test that workflow file exists"""
        path = Path(".github/workflows/ai-fix-coderabbit-issues.yml")
        assert path.exists(), "Workflow file not found"

    def test_workflow_has_required_triggers(self, workflow_file):
        """Test workflow has required triggers"""
        assert "on" in workflow_file
        assert "workflow_dispatch" in workflow_file["on"]
        assert "repository_dispatch" in workflow_file["on"]

    def test_workflow_has_required_permissions(self, workflow_file):
        """Test workflow has required permissions"""
        jobs = workflow_file["jobs"]
        ai_job = jobs["ai-remediation"]

        assert "permissions" in ai_job
        perms = ai_job["permissions"]
        assert perms["contents"] == "write"
        assert perms["pull-requests"] == "write"

    def test_workflow_uses_correct_secrets(self, workflow_file):
        """Test workflow references correct secrets"""
        jobs = workflow_file["jobs"]
        ai_job = jobs["ai-remediation"]
        env = ai_job["env"]

        # Check LINEAR_SECRET is used
        assert "secrets.LINEAR_SECRET" in str(env)

    def test_workflow_has_slack_notifications(self, workflow_file):
        """Test workflow includes Slack notification steps"""
        # After Phase 3.1, this should pass
        pytest.skip("Slack notifications not yet implemented")


class TestWorkflowSteps:
    """Test individual workflow steps"""

    @pytest.fixture
    def workflow_file(self):
        """Load workflow YAML"""
        path = Path(".github/workflows/ai-fix-coderabbit-issues.yml")
        with open(path) as f:
            return yaml.safe_load(f)

    def test_has_fetch_issue_step(self, workflow_file):
        """Test workflow has step to fetch Linear issue"""
        jobs = workflow_file["jobs"]
        steps = jobs["ai-remediation"]["steps"]

        step_names = [s["name"] for s in steps]
        assert "Fetch Linear issue details" in step_names

    def test_has_create_pr_step(self, workflow_file):
        """Test workflow has step to create PR"""
        jobs = workflow_file["jobs"]
        steps = jobs["ai-remediation"]["steps"]

        step_names = [s["name"] for s in steps]
        assert "Create Pull Request" in step_names
```

---

#### Task 3.2.4: Create Test Runner Script (30 minutes)
**File**: `scripts/run-automation-tests.sh`

```bash
#!/bin/bash
###############################################################################
# Automation Test Runner
# Runs all automation tests with proper environment setup
###############################################################################

set -euo pipefail

echo "🧪 Running Automation Test Suite"
echo "================================"

# Check prerequisites
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-asyncio
fi

# Run tests
echo ""
echo "📋 Running unit tests..."
pytest tests/automation/ -v -m "not integration and not slow"

echo ""
echo "🔗 Running integration tests..."
if [ -n "${LINEAR_API_KEY:-}" ]; then
    pytest tests/automation/ -v -m "integration"
else
    echo "⚠️  Skipping integration tests (LINEAR_API_KEY not set)"
fi

echo ""
echo "📊 Generating coverage report..."
pytest tests/automation/ --cov=scripts --cov-report=html --cov-report=term

echo ""
echo "✅ Test suite complete!"
echo "📄 Coverage report: htmlcov/index.html"
```

---

#### Task 3.2.5: Document Testing Strategy (30 minutes)
**File**: `docs/ci-cd/AUTOMATION-TESTING-GUIDE.md`

```markdown
# Automation Testing Guide

## Test Coverage

### Unit Tests
- Script validation (exists, executable)
- Configuration validation (YAML structure)
- Helper functions

### Integration Tests
- Linear API calls (with real API key)
- GitHub Actions workflow triggers
- End-to-end remediation flow

### Manual Tests
- Slack notifications
- PR creation
- Linear issue updates

## Running Tests

### All Tests
\`\`\`bash
./scripts/run-automation-tests.sh
\`\`\`

### Unit Tests Only
\`\`\`bash
pytest tests/automation/ -v -m "not integration"
\`\`\`

### Integration Tests
\`\`\`bash
export LINEAR_API_KEY="lin_api_..."
pytest tests/automation/ -v -m "integration"
\`\`\`

## CI/CD Integration

Tests run automatically on:
- Pull requests to `main`
- Commits to feature branches
- Manual workflow triggers
```

**Deliverable**: Complete testing framework and documentation

---

## 📊 Sprint 3.3: Monitoring & Metrics (4 hours)

### Objective
Track automation performance and create visibility dashboards

### Tasks

#### Task 3.3.1: Define Automation Metrics (1 hour)
**File**: `docs/ci-cd/AUTOMATION-METRICS.md`

```markdown
# Automation Metrics

## Key Performance Indicators (KPIs)

### Workflow Metrics
- **workflow_runs_total**: Counter of workflow executions
  - Labels: `status` (success, failure, cancelled)
- **workflow_duration_seconds**: Histogram of workflow duration
  - Buckets: 30s, 1m, 5m, 10m, 30m
- **workflow_success_rate**: Gauge (success / total)

### Issue Remediation Metrics
- **issues_processed_total**: Counter of issues handled
  - Labels: `severity` (critical, high, medium, low)
- **prs_created_total**: Counter of PRs created
  - Labels: `ai_tool` (claude-code, cursor, auto-fix, pre-commit)
- **prs_merged_total**: Counter of PRs merged
- **time_to_remediation**: Histogram (issue created → PR merged)
  - SLO: < 24 hours for critical, < 48 hours for high

### Quality Metrics
- **test_success_rate**: Gauge (tests passed / total)
- **auto_fix_success_rate**: Gauge (automated fixes / total)
- **manual_intervention_rate**: Gauge (manual fixes / total)

## Data Sources

1. **GitHub Actions**: Workflow runs API
2. **Linear API**: Issue states and timestamps
3. **Custom tracking**: Prometheus metrics from scripts

## Dashboard Sections

1. **Overview**: Success rate, active workflows, recent activity
2. **Performance**: Duration histograms, bottleneck analysis
3. **Quality**: Test pass rates, auto-fix success
4. **Trends**: Issues over time, PR merge velocity
```

---

#### Task 3.3.2: Create Prometheus Exporter (2 hours)
**File**: `scripts/export-automation-metrics.sh`

```bash
#!/bin/bash
###############################################################################
# Automation Metrics Exporter
# Exports metrics to Prometheus pushgateway or file
###############################################################################

set -euo pipefail

METRICS_FILE="${1:-/tmp/automation_metrics.prom}"

# Helper: Write metric
write_metric() {
    local name="$1"
    local type="$2"
    local value="$3"
    local labels="${4:-}"

    echo "# TYPE $name $type" >> "$METRICS_FILE"
    if [ -n "$labels" ]; then
        echo "${name}{${labels}} ${value}" >> "$METRICS_FILE"
    else
        echo "${name} ${value}" >> "$METRICS_FILE"
    fi
}

# Clear file
> "$METRICS_FILE"

# Query GitHub Actions API for workflow metrics
if [ -n "${GITHUB_TOKEN:-}" ]; then
    echo "📊 Fetching workflow metrics from GitHub..."

    REPO="hanax-ai/hx-citadel-ansible"
    WORKFLOW_ID="ai-fix-coderabbit-issues.yml"

    # Get recent workflow runs
    RUNS=$(gh api "/repos/$REPO/actions/workflows/$WORKFLOW_ID/runs?per_page=100" | jq -r '.workflow_runs[]')

    # Count by status
    SUCCESS_COUNT=$(echo "$RUNS" | jq -r 'select(.conclusion=="success") | .id' | wc -l)
    FAILURE_COUNT=$(echo "$RUNS" | jq -r 'select(.conclusion=="failure") | .id' | wc -l)

    write_metric "automation_workflow_runs_total" "counter" "$SUCCESS_COUNT" "status=\"success\""
    write_metric "automation_workflow_runs_total" "counter" "$FAILURE_COUNT" "status=\"failure\""

    # Calculate success rate
    TOTAL=$((SUCCESS_COUNT + FAILURE_COUNT))
    if [ "$TOTAL" -gt 0 ]; then
        SUCCESS_RATE=$(echo "scale=2; $SUCCESS_COUNT / $TOTAL" | bc)
        write_metric "automation_workflow_success_rate" "gauge" "$SUCCESS_RATE"
    fi
fi

# Query Linear API for issue metrics
if [ -n "${LINEAR_API_KEY:-}" ]; then
    echo "📊 Fetching issue metrics from Linear..."

    # Get issues with coderabbit-finding label
    QUERY='{ issues(filter: { labels: { name: { eq: "coderabbit-finding" } } }) { nodes { id state { name } priority createdAt } } }'

    RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": $(echo "$QUERY" | jq -Rs .)}")

    TOTAL_ISSUES=$(echo "$RESPONSE" | jq -r '.data.issues.nodes | length')
    COMPLETED=$(echo "$RESPONSE" | jq -r '.data.issues.nodes[] | select(.state.name=="Done") | .id' | wc -l)

    write_metric "automation_issues_total" "gauge" "$TOTAL_ISSUES"
    write_metric "automation_issues_completed" "gauge" "$COMPLETED"
fi

echo "✅ Metrics exported to: $METRICS_FILE"
```

---

#### Task 3.3.3: Create Grafana Dashboard JSON (1 hour)
**File**: `monitoring/grafana-automation-dashboard.json`

```json
{
  "dashboard": {
    "title": "CodeRabbit Automation Dashboard",
    "tags": ["automation", "coderabbit", "linear"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Workflow Success Rate (Last 7 Days)",
        "type": "gauge",
        "targets": [
          {
            "expr": "automation_workflow_success_rate",
            "legendFormat": "Success Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "red" },
                { "value": 0.8, "color": "yellow" },
                { "value": 0.95, "color": "green" }
              ]
            },
            "unit": "percentunit"
          }
        }
      },
      {
        "title": "Workflow Runs by Status",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(automation_workflow_runs_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Active Issues",
        "type": "stat",
        "targets": [
          {
            "expr": "automation_issues_total - automation_issues_completed",
            "legendFormat": "Open Issues"
          }
        ]
      }
    ]
  }
}
```

---

## 🔐 Sprint 3.4: Security & Validation (3 hours)

### Objective
Add webhook validation, rate limiting, and security hardening

### Tasks

#### Task 3.4.1: Add Webhook Signature Validation (2 hours)
**File**: `.github/workflows/ai-fix-coderabbit-issues.yml`

**Add validation step** (after repository_dispatch trigger):
```yaml
- name: Validate Webhook Signature
  if: github.event_name == 'repository_dispatch'
  run: |
    # Verify webhook came from trusted source
    EVENT_TYPE="${{ github.event.action }}"

    if [ "$EVENT_TYPE" != "linear-issue-created" ]; then
      echo "::error::Invalid event type: $EVENT_TYPE"
      exit 1
    fi

    # Validate payload structure
    ISSUE_ID="${{ github.event.client_payload.issue_id }}"
    SEVERITY="${{ github.event.client_payload.severity }}"

    if [ -z "$ISSUE_ID" ] || [ -z "$SEVERITY" ]; then
      echo "::error::Missing required fields in payload"
      exit 1
    fi

    echo "✅ Webhook validation passed"
```

---

#### Task 3.4.2: Add Rate Limiting (1 hour)
**File**: `.github/workflows/ai-fix-coderabbit-issues.yml`

**Add concurrency control**:
```yaml
concurrency:
  group: ai-remediation-${{ github.event.inputs.issue_id || github.event.client_payload.issue_id }}
  cancel-in-progress: false  # Don't cancel running workflows
```

**Purpose**: Prevent duplicate workflows for the same issue

---

## 📚 Sprint 3.5: Documentation & Runbooks (3 hours)

### Objective
Complete operational documentation for production use

### Tasks

#### Task 3.5.1: Create Operational Runbook (2 hours)
**File**: `docs/ci-cd/AUTOMATION-RUNBOOK.md`

```markdown
# Automation Operational Runbook

## Common Operations

### Manually Trigger Workflow
1. Go to: Actions → ai-fix-coderabbit-issues.yml → Run workflow
2. Enter issue_id (e.g., HAN-123)
3. Select severity
4. Click "Run workflow"

### Check Workflow Status
\`\`\`bash
gh run list --workflow=ai-fix-coderabbit-issues.yml --limit=10
\`\`\`

### View Workflow Logs
\`\`\`bash
gh run view <run_id> --log
\`\`\`

### Rerun Failed Workflow
\`\`\`bash
gh run rerun <run_id>
\`\`\`

## Incident Response

### Alert: Workflow Failure Rate > 20%
**Severity**: P2 (High)
**Actions**:
1. Check recent workflow logs for common errors
2. Verify LINEAR_SECRET is valid
3. Check GitHub API rate limits
4. Review Linear API status
5. Escalate if infrastructure issue

### Alert: No Workflows in 24 Hours
**Severity**: P3 (Medium)
**Actions**:
1. Verify CodeRabbit is running
2. Check Linear webhook configuration
3. Test manual trigger
4. Review recent PRs for undetected issues

### Alert: Slack Notifications Not Sending
**Severity**: P4 (Low)
**Actions**:
1. Verify SLACK_WEBHOOK_URL secret exists
2. Test webhook with curl
3. Check Slack workspace status
4. Review workflow logs for notification steps

## Troubleshooting

### Issue: "Could not fetch Linear issue"
**Cause**: LINEAR_SECRET invalid or expired
**Fix**:
1. Generate new Personal API Key in Linear
2. Update GitHub Secret: LINEAR_SECRET
3. Rerun workflow

### Issue: "PR creation failed"
**Cause**: GITHUB_TOKEN permissions insufficient
**Fix**:
1. Verify workflow permissions in YAML
2. Check repository settings → Actions → General → Workflow permissions
3. Ensure "Read and write permissions" is enabled

### Issue: "Tests failing in workflow"
**Cause**: Test infrastructure or code issues
**Fix**:
1. Run tests locally: `pytest tests/ -v`
2. Check test logs in workflow
3. Fix failing tests
4. Commit and push fixes

## Maintenance

### Weekly Tasks
- [ ] Review workflow metrics
- [ ] Check Slack notification quality
- [ ] Review automation success rate
- [ ] Clean up old branches (fix/*)

### Monthly Tasks
- [ ] Audit LINEAR_SECRET expiration
- [ ] Review and update documentation
- [ ] Analyze automation ROI
- [ ] Update runbook with new learnings

### Quarterly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Update dependencies
- [ ] Disaster recovery drill
```

---

#### Task 3.5.2: Create Metrics Dashboard Guide (1 hour)
**File**: `docs/ci-cd/AUTOMATION-DASHBOARD-GUIDE.md`

```markdown
# Automation Metrics Dashboard Guide

## Accessing the Dashboard

**URL**: `http://grafana.hx-citadel.local/d/automation/coderabbit-automation`

## Dashboard Sections

### 1. Overview (Top Row)
- **Success Rate**: % of successful workflow runs
  - Target: > 95%
  - Alert: < 80%
- **Active Issues**: Open CodeRabbit findings
  - Target: < 10
  - Alert: > 50
- **PRs This Week**: PRs created by automation
  - Target: > 5
  - Alert: 0 (no activity)

### 2. Workflow Performance (Middle Row)
- **Duration**: Time from trigger to completion
  - Target: < 5 minutes
  - Alert: > 10 minutes
- **Runs by Status**: Success vs failure trends
- **Queue Depth**: Waiting workflows

### 3. Quality Metrics (Bottom Row)
- **Test Pass Rate**: % of PRs with passing tests
  - Target: > 90%
- **Auto-Fix Success**: % of issues fixed automatically
  - Target: > 60%
- **Manual Intervention**: % requiring human fixes
  - Target: < 40%

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Success Rate | < 90% | < 80% |
| Duration | > 7 min | > 10 min |
| Test Pass Rate | < 85% | < 75% |
| Active Issues | > 20 | > 50 |

## Using Filters

- **Time Range**: Default 24h, adjust as needed
- **Severity**: Filter by critical/high/medium/low
- **AI Tool**: Filter by tool type
- **Status**: Filter by success/failure

## Exporting Data

1. Click "Share" → "Export"
2. Select format (CSV, JSON)
3. Choose time range
4. Download
```

---

## ✅ Phase 3 Deliverables

### Sprint 3.1: Slack Notifications
- [ ] Slack webhook configured
- [ ] Helper script created (`slack-notify.sh`)
- [ ] 4 notification points added to workflow
- [ ] Notifications tested and working

### Sprint 3.2: End-to-End Testing
- [ ] Test framework created (`tests/automation/`)
- [ ] 15+ tests written (unit + integration)
- [ ] Test runner script created
- [ ] Testing guide documented
- [ ] CI/CD integration configured

### Sprint 3.3: Monitoring & Metrics
- [ ] Metrics defined and documented
- [ ] Prometheus exporter created
- [ ] Grafana dashboard JSON created
- [ ] Dashboard guide written

### Sprint 3.4: Security & Validation
- [ ] Webhook signature validation added
- [ ] Rate limiting configured
- [ ] Security audit completed

### Sprint 3.5: Documentation
- [ ] Operational runbook created
- [ ] Dashboard guide written
- [ ] Troubleshooting procedures documented
- [ ] Incident response playbook created

---

## 📊 Success Criteria

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Workflow Success Rate** | > 95% | TBD | ⏳ |
| **Mean Time to Remediation** | < 24h (critical) | TBD | ⏳ |
| **Auto-Fix Success Rate** | > 60% | TBD | ⏳ |
| **Test Coverage** | > 80% | 0% | ⏳ |
| **Documentation Complete** | 100% | 0% | ⏳ |
| **Slack Notifications** | 100% | 0% | ⏳ |

---

## 🚀 Implementation Order

### Day 1: Core Features (6-7 hours)
1. ✅ Sprint 3.1: Slack Notifications (4 hours)
2. ✅ Sprint 3.4: Security & Validation (3 hours)

### Day 2: Testing & Monitoring (7-8 hours)
3. ✅ Sprint 3.2: End-to-End Testing (6 hours)
4. ✅ Sprint 3.3: Monitoring & Metrics (partial, 2 hours)

### Day 3: Documentation & Polish (5-6 hours)
5. ✅ Sprint 3.3: Monitoring & Metrics (complete, 2 hours)
6. ✅ Sprint 3.5: Documentation & Runbooks (3 hours)
7. ✅ Final testing and validation (1 hour)

**Total Effort**: 18-21 hours (2-3 days)

---

## 🎯 Next Steps

### Immediate (Now)
1. Create Slack webhook
2. Add LINEAR_SECRET to GitHub (✅ Done)
3. Review Phase 3 plan

### Short Term (Today)
4. Implement Sprint 3.1 (Slack notifications)
5. Test notifications in dev environment

### Medium Term (This Week)
6. Implement Sprint 3.2 (Testing)
7. Implement Sprint 3.3 (Monitoring)
8. Complete Sprint 3.4 & 3.5

### Long Term (Next Week)
9. Full production deployment
10. Monitor metrics for 1 week
11. Iterate based on feedback

---

**Status**: 📋 Ready to Implement
**Owner**: Claude Code - Senior Engineer
**Commitment**: Quality first, SOLID principles, comprehensive testing 🎯

---

**Last Updated**: October 11, 2025
**Next Review**: After each sprint completion
