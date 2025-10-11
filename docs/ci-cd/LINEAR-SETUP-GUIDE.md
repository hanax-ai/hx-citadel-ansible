# Linear + CodeRabbit Integration Setup Guide

**Created**: October 11, 2025  
**Status**: ✅ API Key Validated  
**Team**: HANA-X Ai (HAN)

---

## ✅ Setup Status

| Step | Status | Details |
|------|--------|---------|
| **Generate Linear API Key** | ✅ Complete | `lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH` |
| **Validate API Key** | ✅ Complete | User: jarvisr@hana-x.ai (Admin) |
| **Find Team ID** | ✅ Complete | Team: HANA-X Ai, Key: HAN, ID: 82355734-bc0c-49c6-ba88-6ad2ca50865a |
| **Update CodeRabbit Config** | ✅ Complete | `.coderabbit.yaml` updated with team_key |
| **Secure API Key** | ✅ Complete | Saved to `.env.linear` (mode 600, in .gitignore) |
| **Configure GitHub Secret** | ⏳ Next | Add to GitHub repository secrets |
| **Test Integration** | ⏳ Next | Create test PR |

---

## Linear Workspace Details

```yaml
Team Name: HANA-X Ai
Team Key: HAN
Team ID: 82355734-bc0c-49c6-ba88-6ad2ca50865a
API User: jarvisr@hana-x.ai
API Role: Admin
API Key: lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH
```

**⚠️ SECURITY**: API key stored in:
- Local: `.env.linear` (mode 600, git-ignored)
- GitHub: Will be added as repository secret `LINEAR_API_KEY`

---

## API Validation Test Results

```bash
# Test 1: Verify user authentication
$ curl -X POST https://api.linear.app/graphql \
  -H "Authorization: lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email admin } }"}'

✅ Result:
{
  "data": {
    "viewer": {
      "name": "jarvisr@hana-x.ai",
      "email": "jarvisr@hana-x.ai",
      "admin": true
    }
  }
}
```

```bash
# Test 2: Query available teams
$ curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query Teams { teams { nodes { id name key } } }"}'

✅ Result:
{
  "data": {
    "teams": {
      "nodes": [
        {
          "id": "82355734-bc0c-49c6-ba88-6ad2ca50865a",
          "name": "HANA-X Ai",
          "key": "HAN"
        }
      ]
    }
  }
}
```

---

## Next Steps: Complete GitHub Integration

### 1. Add Linear API Key to GitHub Secrets

Navigate to your GitHub repository:
```
https://github.com/YOUR_ORG/hx-citadel-ansible/settings/secrets/actions
```

**Add new repository secret:**
- Name: `LINEAR_API_KEY`
- Value: `lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH`

### 2. Configure CodeRabbit Web Interface

1. Go to https://app.coderabbit.ai/
2. Navigate to your repository settings
3. Under "Integrations" → "Linear":
   - Enable Linear integration
   - Enter API key: `lin_api_yRumHPpiFUsdPbbng56xSVwX97HCtyTdFvI2OzlH`
   - Select team: **HANA-X Ai (HAN)**
   - Test connection

### 3. Create Linear Labels

In Linear (https://linear.app/), create these labels:
- `coderabbit-finding` (color: #FF6B6B)
- `auto-generated` (color: #4ECDC4)
- `critical` (color: #FF0000)
- `high` (color: #FFA500)
- `security` (color: #8B0000)

### 4. Test Integration with a PR

Create a test PR:
```bash
git checkout -b test/coderabbit-linear-integration
echo "# Test PR for CodeRabbit + Linear" > test-integration.md
git add test-integration.md
git commit -m "test: Validate CodeRabbit + Linear integration"
git push origin test/coderabbit-linear-integration
```

**Expected behavior:**
- CodeRabbit reviews the PR
- If critical/high issues found → Auto-creates Linear issues
- Linear issues link back to the PR
- GitHub PR shows Linear issue references

---

## Integration Configuration

### CodeRabbit (.coderabbit.yaml)

```yaml
integrations:
  linear:
    enabled: true
    team_key: "HAN"
    
    auto_create_issue:
      enabled: true
      severity_levels:
        - critical
        - high
      
      title_template: "[CodeRabbit] {finding_type}: {file_name}"
      
      labels:
        - "coderabbit-finding"
        - "auto-generated"
      
      priority_mapping:
        critical: 1  # Urgent
        high: 2      # High
        medium: 3    # Medium
        low: 4       # Low
    
    issue_linking:
      enabled: true
      validate_against_board: true
```

### Severity → Linear Issue Mapping

| CodeRabbit Severity | Linear Priority | Auto-Create? | Example |
|---------------------|-----------------|--------------|---------|
| **Critical** | 1 (Urgent) | ✅ Yes | Security vulnerability, data loss risk |
| **High** | 2 (High) | ✅ Yes | Performance issue, missing error handling |
| **Medium** | 3 (Medium) | ❌ No | Code duplication, missing docstring |
| **Low** | 4 (Low) | ❌ No | Formatting, naming conventions |

---

## Testing the Integration

### Test 1: Create a Linear Issue Manually

```bash
# Source the API key
source .env.linear

# Create a test issue
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation IssueCreate { issueCreate(input: { title: \"[CodeRabbit Test] Integration Validation\", description: \"Testing CodeRabbit + Linear integration\", teamId: \"82355734-bc0c-49c6-ba88-6ad2ca50865a\", priority: 2 }) { success issue { id identifier url } } }"
  }'
```

**Expected output:**
```json
{
  "data": {
    "issueCreate": {
      "success": true,
      "issue": {
        "id": "...",
        "identifier": "HAN-123",
        "url": "https://linear.app/hana-x/issue/HAN-123/..."
      }
    }
  }
}
```

### Test 2: Trigger CodeRabbit Review with Critical Finding

Create a file with a known critical issue:

```python
# test_security_issue.py
password = "hardcoded_password_123"  # CRITICAL: Plaintext secret
```

**Expected:**
1. CodeRabbit detects critical issue (plaintext secret)
2. CodeRabbit auto-creates Linear issue: `HAN-XXX`
3. Linear issue includes:
   - Title: `[CodeRabbit] no-plaintext-secrets: test_security_issue.py`
   - Priority: 1 (Urgent)
   - Labels: `coderabbit-finding`, `auto-generated`, `security`
   - Description: Link to PR, file, line number
4. PR comment includes Linear issue link

---

## Troubleshooting

### Issue: "Linear API authentication failed"

**Check:**
```bash
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name } }"}'
```

**Expected:** Should return viewer name. If not, regenerate API key.

### Issue: "Team not found"

**Check team ID:**
```bash
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query Teams { teams { nodes { id name key } } }"}'
```

**Verify:** Team ID in `.coderabbit.yaml` matches.

### Issue: "Issues not being created"

**Check CodeRabbit config:**
1. Verify `.coderabbit.yaml` has `auto_create_issue.enabled: true`
2. Verify severity levels include the finding type
3. Check CodeRabbit web interface has Linear connected
4. Verify GitHub secret `LINEAR_API_KEY` is set

---

## Manual Issue Creation Script

For testing or manual issue creation:

```bash
#!/bin/bash
# create-linear-issue.sh

source .env.linear

TITLE="$1"
DESCRIPTION="$2"
PRIORITY="${3:-2}"  # Default: High

curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mutation IssueCreate { issueCreate(input: { title: \\\"$TITLE\\\", description: \\\"$DESCRIPTION\\\", teamId: \\\"82355734-bc0c-49c6-ba88-6ad2ca50865a\\\", priority: $PRIORITY }) { success issue { id identifier url } } }\"
  }"
```

**Usage:**
```bash
./create-linear-issue.sh \
  "[CodeRabbit] Test Issue" \
  "Testing manual issue creation" \
  2
```

---

## Success Criteria

Integration is successful when:

- [x] Linear API key validated
- [x] Team ID confirmed
- [x] CodeRabbit config updated
- [ ] GitHub secret added
- [ ] CodeRabbit web interface connected
- [ ] Test PR triggers review
- [ ] Critical finding auto-creates Linear issue
- [ ] Linear issue links back to PR
- [ ] Issue has correct priority and labels

---

## Related Documentation

- [CodeRabbit + Linear Integration Guide](cr-and-linear-int.md)
- [Automation Workflow](automation-workflow.md)
- [CodeRabbit Configuration](.coderabbit.yaml)

---

**Status**: ✅ Phase 1 Complete (API validation)  
**Next**: Phase 2 (GitHub secrets + CodeRabbit web config)  
**Last Updated**: October 11, 2025

