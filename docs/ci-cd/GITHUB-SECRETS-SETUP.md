# GitHub Secrets Setup Guide
**Purpose**: Configure repository secrets for CodeRabbit + Linear automation
**Date**: October 11, 2025
**Status**: Required for Phase 2B AI-Assisted Remediation

---

## Overview

The AI remediation workflow (`.github/workflows/ai-fix-coderabbit-issues.yml`) requires **two secrets** to be configured in GitHub repository settings:

1. **`LINEAR_API_KEY`** - Personal API Key for Linear GraphQL API
2. **`GITHUB_TOKEN`** - Automatically provided by GitHub Actions (no setup needed)

---

## Step 1: Add LINEAR_API_KEY to GitHub Secrets

### Navigate to Repository Settings

1. **Go to repository**: `https://github.com/hanax-ai/hx-citadel-ansible`
2. **Click Settings** (top menu bar)
3. **Navigate to**: `Settings → Secrets and variables → Actions`
4. **Click**: "New repository secret" (green button)

### Create the Secret

**Field 1 - Name**:
```
LINEAR_API_KEY
```

**Field 2 - Secret** (paste the working API key):
```
lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH
```

**Click**: "Add secret" (green button)

### ✅ Verification

After adding, you should see:
```
LINEAR_API_KEY    Updated 1 minute ago
```

⚠️ **Important**: Once saved, you **cannot view the secret value** again. If you need to verify it, you must:
- Delete the secret
- Re-create it with the correct value

---

## Step 2: Verify GITHUB_TOKEN (Automatic)

The `GITHUB_TOKEN` secret is **automatically provided** by GitHub Actions with these permissions (configured in workflow):

```yaml
permissions:
  contents: write       # Push commits to branches
  pull-requests: write  # Create/update PRs
  issues: write         # Update Linear issues (optional)
```

✅ **No action required** - GitHub handles this automatically.

---

## How the Workflow Uses These Secrets

### LINEAR_API_KEY Usage

The workflow uses `LINEAR_API_KEY` in **two places**:

#### 1. Fetch Linear Issue Details (Step: "Fetch Linear issue details")
```bash
# Uses helper script with LINEAR_API_KEY environment variable
ISSUE_JSON=$(./scripts/fetch-linear-issue.sh "$ISSUE_ID")
```

#### 2. Update Linear Issue with PR Link (Step: "Update Linear issue with PR link")
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$MUTATION" | jq -Rs .)}"
```

⚠️ **Critical**: The workflow uses `Authorization: $LINEAR_API_KEY` (NO "Bearer" prefix)

### GITHUB_TOKEN Usage

The workflow uses `GITHUB_TOKEN` for:

#### 1. Create Pull Request (Step: "Create Pull Request")
```yaml
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
run: |
  gh pr create \
    --title "Fix ${{ steps.linear.outputs.identifier }}: ..." \
    --body "$PR_BODY" \
    --label "coderabbit-fix,ai-generated"
```

#### 2. Push Branch to Remote
```bash
git push -u origin "$branch_name"
```

---

## Testing the Configuration

### Test 1: Manual Workflow Trigger

**Purpose**: Verify secrets are configured correctly

**Steps**:
1. Go to: `https://github.com/hanax-ai/hx-citadel-ansible/actions/workflows/ai-fix-coderabbit-issues.yml`
2. Click: "Run workflow" (dropdown button)
3. Fill in:
   - **issue_id**: `HAN-5`
   - **severity**: `high`
4. Click: "Run workflow" (green button)

**Expected Result**:
- ✅ Workflow runs successfully
- ✅ Fetches Linear issue HAN-5
- ✅ Creates branch `fix/han-5`
- ✅ Routes to `claude-code` (no changes expected)
- ✅ Creates PR (empty, no commits)

**If it fails**:
- Check "Fetch Linear issue details" step logs
- Look for: `Error: Could not fetch issue details`
- This means LINEAR_API_KEY is missing or incorrect

---

### Test 2: Verify API Key with curl

**Purpose**: Test LINEAR_API_KEY directly before adding to GitHub

**Local Test**:
```bash
# Export the key (on your local machine)
export LINEAR_API_KEY="lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH"

# Test authentication
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email } }"}'
```

**Expected Response**:
```json
{
  "data": {
    "viewer": {
      "name": "Your Name",
      "email": "your@email.com"
    }
  }
}
```

**If you get an error**:
```json
{
  "errors": [{
    "message": "Authentication required, not authenticated"
  }]
}
```

This means:
- API key is incorrect
- API key lacks required permissions
- Create a new Personal API Key with **full permissions**

---

## Troubleshooting

### Error: "LINEAR_API_KEY environment variable not set"

**Cause**: Secret not added to GitHub or wrong name

**Fix**:
1. Go to: `Settings → Secrets and variables → Actions`
2. Verify secret exists: `LINEAR_API_KEY`
3. If missing, add it with exact name (case-sensitive)
4. If exists but still failing, delete and re-create

---

### Error: "Could not fetch issue details"

**Cause 1**: API key lacks permissions

**Fix**:
1. Go to: `https://linear.app/settings/api`
2. Delete the existing Personal API Key
3. Create NEW key with **full permissions** (select all checkboxes)
4. Copy key immediately (starts with `lin_api_`)
5. Update GitHub Secret with new key

**Cause 2**: Issue ID format incorrect

**Fix**:
- Use human-friendly format: `HAN-5` (not global ID)
- Check team key: `HAN` for HANA-X Ai team
- Verify issue exists in Linear workspace

---

### Error: "gh: command not found"

**Cause**: GitHub CLI not available in runner (unlikely - ubuntu-latest includes it)

**Fix**:
Add installation step before PR creation:
```yaml
- name: Install GitHub CLI
  run: |
    sudo apt-get update
    sudo apt-get install -y gh
```

---

### Error: "fatal: could not read Password for 'https://github.com'"

**Cause**: GITHUB_TOKEN permissions insufficient

**Fix**:
Verify workflow permissions (should already be set):
```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
```

---

## Security Best Practices

### ✅ DO:
- Store LINEAR_API_KEY in GitHub Secrets (encrypted at rest)
- Use Personal API Keys (not OAuth tokens) for scripts
- Rotate API keys periodically (every 90 days recommended)
- Create keys with **minimum required permissions**

### ❌ DON'T:
- Never commit API keys to git
- Never log API keys in workflow output
- Never expose keys in PR descriptions
- Never share keys across multiple repositories (1 key per repo)

---

## Key Permissions Required

### LINEAR_API_KEY Permissions

When creating the Personal API Key in Linear, ensure these scopes are selected:

✅ **Read permissions** (minimum):
- ✅ Read issues
- ✅ Read teams
- ✅ Read users

✅ **Write permissions** (for full automation):
- ✅ Write issues (for status updates)
- ✅ Write comments (for PR link updates)

**Recommended**: Select "Full access" when creating the key to avoid permission issues.

---

## Workflow Trigger Methods

### Method 1: Manual Trigger (workflow_dispatch)

**When**: Testing, one-off fixes, debugging

**How**:
```
GitHub Actions → ai-fix-coderabbit-issues.yml → Run workflow
Inputs:
  - issue_id: "HAN-5"
  - severity: "high"
```

### Method 2: CodeRabbit Webhook (repository_dispatch)

**When**: Automated - CodeRabbit creates Linear issue

**How**:
1. CodeRabbit detects critical/high severity finding
2. Creates Linear issue via `.coderabbit.yaml` config
3. Sends `repository_dispatch` event to GitHub
4. Workflow triggers automatically

**Event Payload**:
```json
{
  "event_type": "linear-issue-created",
  "client_payload": {
    "issue_id": "HAN-123",
    "severity": "critical"
  }
}
```

---

## Next Steps

1. ✅ Add `LINEAR_API_KEY` to GitHub Secrets (this guide)
2. ⏭️ Test workflow with manual trigger (`HAN-5`)
3. ⏭️ Verify PR creation works
4. ⏭️ Test CodeRabbit auto-trigger (create test PR with issues)
5. ⏭️ Enable Linear webhook integration (Phase 2B final step)

---

## Reference Links

- **GitHub Secrets Documentation**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Linear API Documentation**: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- **Linear API Key Guide**: `docs/ci-cd/LINEAR-API-KEY-GUIDE.md`
- **Workflow Test Report**: `docs/ci-cd/LINEAR-WORKFLOW-TEST-REPORT.md`

---

**Last Updated**: October 11, 2025
**Maintained By**: HX-Citadel Development Team
**Status**: Ready for production use ✅
