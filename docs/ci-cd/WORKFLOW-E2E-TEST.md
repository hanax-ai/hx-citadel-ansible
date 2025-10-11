# CI/CD Workflow End-to-End Test Plan

**Date**: October 11, 2025  
**Test Type**: Integration & End-to-End  
**Workflow Under Test**: AI Fix CodeRabbit Issues  
**Test Environment**: Production GitHub Actions

---

## Test Objectives

1. ✅ Verify workflow can be triggered successfully
2. ✅ Validate all secrets are accessible
3. ✅ Test Linear API integration
4. ✅ Verify script execution
5. ✅ Test error handling and notifications
6. ✅ Validate PR creation flow

---

## Prerequisites Check

### 1. GitHub CLI Authentication
```bash
gh auth status
```
**Expected**: ✅ Authenticated with workflow permissions

### 2. Required Secrets
```bash
gh secret list
```
**Expected**: ✅ All secrets configured
- `LINEAR_SECRET` ✅
- `GITHUB_TOKEN` (auto-provided) ✅
- `CLAUDE_CODE_OAUTH_TOKEN` ✅
- `SLACK_WEBHOOK_URL` ✅

### 3. Workflow Status
```bash
gh workflow list
```
**Expected**: ✅ "AI Fix CodeRabbit Issues" is active

---

## Test Scenarios

### Scenario 1: Linear API Connection Test
**Objective**: Verify LINEAR_SECRET is valid and API is accessible

```bash
# Test script exists
./scripts/test-linear-api.sh
```

**Expected Results**:
- ✅ API authentication successful
- ✅ Teams fetched
- ✅ Team keys displayed

---

### Scenario 2: Script Validation Test
**Objective**: Verify all required scripts are present and executable

```bash
# Check script permissions
ls -la scripts/*.sh | grep -E "(slack-notify|fetch-linear-issue|fix-linear-issue|test-linear-api)"

# Validate syntax
bash -n scripts/fetch-linear-issue.sh
bash -n scripts/fix-linear-issue.sh
bash -n scripts/slack-notify.sh
bash -n scripts/test-linear-api.sh
```

**Expected Results**:
- ✅ All scripts are executable (-rwxrwxr-x)
- ✅ No syntax errors

---

### Scenario 3: Workflow Dry Run (Manual Trigger)
**Objective**: Trigger workflow manually with test parameters

#### Test Case 3.1: Critical Severity Issue

```bash
gh workflow run "AI Fix CodeRabbit Issues" \
  --field issue_id="TEST-001" \
  --field severity="critical"
```

**Expected Behavior**:
1. Workflow should start
2. Circuit breaker passes (not an ai-fix branch)
3. Severity check passes (critical)
4. Attempts to fetch Linear issue TEST-001
5. May fail at Linear fetch (expected - test issue doesn't exist)
6. Error notification sent to Slack (if configured)

#### Test Case 3.2: Low Severity (Should Skip)

```bash
gh workflow run "AI Fix CodeRabbit Issues" \
  --field issue_id="TEST-002" \
  --field severity="low"
```

**Expected Behavior**:
1. Workflow starts
2. Severity check fails (low priority)
3. Workflow skips remaining steps
4. No errors reported

---

### Scenario 4: Fetch Real Linear Issue (Read-Only)
**Objective**: Test Linear API with a real issue ID

**Prerequisites**: You need a real Linear issue ID from your team

```bash
# First, get your team key
./scripts/test-linear-api.sh

# Then fetch a real issue (replace TEAM-123 with actual issue)
./scripts/fetch-linear-issue.sh "TEAM-123"
```

**Expected Results**:
- ✅ Issue data fetched successfully
- ✅ JSON response with issue details
- ✅ Labels and severity visible

---

### Scenario 5: End-to-End Full Workflow Test
**Objective**: Complete workflow execution with a real Linear issue

**⚠️ WARNING**: This will create a real branch and PR!

#### Prerequisites:
1. Create a test Linear issue with:
   - Title: "Test: AI workflow end-to-end test"
   - Label: `coderabbit-quality` (low risk, uses cursor tool)
   - Priority: High
   - Description: "Test issue for CI/CD workflow validation"

2. Get the issue ID from Linear (e.g., `DEV-123`)

#### Execute Test:

```bash
# Trigger workflow with real issue
gh workflow run "AI Fix CodeRabbit Issues" \
  --field issue_id="DEV-123" \
  --field severity="high"

# Monitor execution
gh run watch

# View results
gh run list --workflow="AI Fix CodeRabbit Issues" --limit 1
```

**Expected Flow**:
1. ✅ Workflow triggered
2. ✅ Slack notification: "Workflow Started"
3. ✅ Linear issue fetched
4. ✅ AI tool determined (cursor for coderabbit-quality)
5. ✅ Fix branch created: `dev-123-ai-fix`
6. ⚠️ No changes generated (expected - test issue has no code context)
7. ✅ Slack notification: "No Changes Generated"
8. ✅ Workflow completes without errors

#### Cleanup:
```bash
# Delete test branch if created
git push origin --delete dev-123-ai-fix 2>/dev/null || echo "No branch to delete"

# Close/delete test Linear issue
```

---

### Scenario 6: Error Handling Tests
**Objective**: Verify workflow handles errors gracefully

#### Test Case 6.1: Invalid Issue ID

```bash
gh workflow run "AI Fix CodeRabbit Issues" \
  --field issue_id="INVALID-999" \
  --field severity="critical"
```

**Expected**:
- ⚠️ Linear API returns error
- ✅ Workflow catches error
- ✅ Slack notification: "Workflow Failed"
- ✅ Error logged in workflow summary

#### Test Case 6.2: Missing Secret (Simulated)

**Note**: Cannot actually test without removing secret, but workflow should fail gracefully

**Expected Behavior**:
- ❌ Linear API call fails (401 Unauthorized)
- ✅ Error caught and reported
- ✅ Workflow marked as failed

---

### Scenario 7: Notification Tests
**Objective**: Verify Slack notifications work

#### Test Case 7.1: Check Slack Script

```bash
# Test slack-notify.sh exists and is executable
[ -x "./scripts/slack-notify.sh" ] && echo "✅ Script executable" || echo "❌ Script not executable"

# Test script syntax
bash -n ./scripts/slack-notify.sh && echo "✅ Valid syntax" || echo "❌ Syntax error"
```

#### Test Case 7.2: Manual Slack Test (Optional)

**⚠️ Only if you want to test Slack webhook directly**

```bash
# Get webhook URL (securely)
echo "Slack webhook is configured: $(gh secret list | grep SLACK_WEBHOOK_URL | wc -l) secret(s)"

# Note: Don't expose the actual webhook URL in logs
```

---

### Scenario 8: Parallel Test Execution
**Objective**: Verify tests run in parallel (pytest, mypy, ansible-lint)

**Note**: This requires a workflow run that makes code changes

**Expected**:
- ✅ Three test steps run simultaneously
- ✅ Each uses `continue-on-error: true`
- ✅ Results aggregated in PR body
- ✅ PR created even if tests fail

---

### Scenario 9: Circuit Breaker Test
**Objective**: Verify workflow skips on ai-fix branches

```bash
# Create a test ai-fix branch
git checkout -b test-123-ai-fix
git push origin test-123-ai-fix

# Try to trigger workflow (should be skipped by circuit breaker)
# Note: workflow_dispatch doesn't check branch, but push would
```

**Expected**:
- ✅ Circuit breaker condition prevents execution
- ✅ No wasted runner minutes

**Cleanup**:
```bash
git checkout main
git push origin --delete test-123-ai-fix
```

---

### Scenario 10: YAML Validation Test
**Objective**: Verify workflow YAML is valid

```bash
# Parse YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ai-fix-coderabbit-issues.yml'))" && \
  echo "✅ YAML is valid" || echo "❌ YAML syntax error"

# Check with yamllint
yamllint .github/workflows/ai-fix-coderabbit-issues.yml 2>&1 | grep -i error || \
  echo "✅ No critical YAML errors"
```

**Expected**:
- ✅ YAML parses successfully
- ⚠️ May have warnings (line length, etc.) but no errors

---

## Test Execution Log

### Test Run 1: [Date/Time]

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| Prerequisites Check | ⏳ Pending | |
| Linear API Connection | ⏳ Pending | |
| Script Validation | ⏳ Pending | |
| Workflow Dry Run (Critical) | ⏳ Pending | |
| Workflow Dry Run (Low) | ⏳ Pending | |
| Fetch Real Issue | ⏳ Pending | |
| End-to-End Test | ⏳ Pending | |
| Error Handling | ⏳ Pending | |
| Notification Tests | ⏳ Pending | |
| YAML Validation | ⏳ Pending | |

---

## Success Criteria

### Minimum Viable (Must Pass)
- ✅ Workflow can be triggered
- ✅ Linear API connection works
- ✅ Scripts are executable and syntax-valid
- ✅ YAML parses correctly
- ✅ Circuit breaker works
- ✅ Severity filtering works

### Full Success (Should Pass)
- ✅ Real Linear issue can be fetched
- ✅ Branch creation works
- ✅ PR creation works
- ✅ Slack notifications sent
- ✅ Error handling graceful
- ✅ Test results reported correctly

### Optional (Nice to Have)
- ✅ AI tool actually generates fixes
- ✅ Tests pass on generated code
- ✅ PR can be auto-merged

---

## Known Limitations (Phase 2B)

1. **Claude Code Integration**: Manual placeholder (not automated)
   - Workflow creates PR template
   - Human intervention required

2. **Auto-Fix Tool**: Basic implementation
   - Type hints auto-fix is TODO
   - Currently just runs mypy

3. **No Auto-Merge**: All PRs require manual review
   - Even if all tests pass
   - Phase 3 feature

---

## Rollback Plan

If tests reveal critical issues:

1. **Disable Workflow**:
   ```bash
   gh workflow disable "AI Fix CodeRabbit Issues"
   ```

2. **Revert Recent Changes**:
   ```bash
   git revert HEAD~3..HEAD  # Revert last 3 commits
   git push origin main
   ```

3. **Notify Team**:
   - Update Linear tickets
   - Post in Slack channel
   - Document issues found

---

## Post-Test Actions

### After Successful Test:
1. ✅ Document any issues found
2. ✅ Update audit report if needed
3. ✅ Create Linear tickets for improvements
4. ✅ Update team documentation
5. ✅ Schedule next test (monthly)

### After Failed Test:
1. ❌ Document failure mode
2. ❌ Create critical bug ticket
3. ❌ Disable workflow if necessary
4. ❌ Implement fixes
5. ❌ Re-test before re-enabling

---

## Monitoring & Observability

### During Test:
```bash
# Watch workflow execution
gh run watch

# View logs in real-time
gh run view --log

# Check recent runs
gh run list --workflow="AI Fix CodeRabbit Issues" --limit 5
```

### Metrics to Track:
- Workflow execution time
- Success/failure rate
- Linear API latency
- PR creation time
- Test execution time

---

## Contact & Support

**Test Owner**: DevOps Team  
**Escalation**: DevOps Team Lead  
**Documentation**: `/docs/ci-cd/`  
**Issues**: Create Linear ticket with label `ci-cd-workflow`

---

**Test Plan Version**: 1.0  
**Last Updated**: October 11, 2025  
**Next Review**: After Phase 3 implementation

