# Phase 2A Deployment Checklist
## CodeRabbit Automation - Manual Remediation

**Status**: 🚀 IN PROGRESS
**Started**: October 11, 2025
**Target Completion**: October 15, 2025 (Week 1)
**Owner**: DevOps Team

---

## ✅ Pre-Deployment (COMPLETE)

- [x] **Organize documentation**
  - Created `docs/ci-cd/` subdirectory
  - Moved CodeRabbit docs to CI/CD folder
  - Created CI/CD README

- [x] **Create automation files**
  - `.coderabbit.yaml` (350+ lines) - Nitpick filtering, auto-issue creation
  - `scripts/fix-linear-issue.sh` (350+ lines) - AI routing and remediation
  - `.github/workflows/ai-fix-coderabbit-issues.yml` (250+ lines) - GitHub Action

- [x] **Commit to repository**
  - Commit: `a4c4b82` - "feat: Add CodeRabbit automation with Linear integration"
  - Branch: `feature/phase2-automated-testing`
  - Files: 8 changed, 2,476 insertions

---

## 🔧 Configuration (IN PROGRESS)

### Step 1: Enable Linear Integration ⏸️ PENDING

**Time**: 5 minutes
**Owner**: DevOps Lead (requires admin access)

**Instructions**:
1. Visit https://app.coderabbit.ai/settings/integrations
2. Find "Linear" in integrations list
3. Click "Enable Linear Integration"
4. Click "Authorize" and select your Linear workspace
5. Grant permissions:
   - Read issues
   - Create issues
   - Update issues
   - Read/write comments
6. Confirm authorization

**Verification**:
```bash
# Test by creating a PR with known issue
# CodeRabbit should auto-create Linear issue if critical/high
```

**Status**: ⏸️ Awaiting user action

---

### Step 2: Create Linear Labels ⏸️ PENDING

**Time**: 3 minutes
**Owner**: Linear Admin

**Instructions**:
1. Visit https://linear.app/[workspace]/settings/labels
2. Create 6 labels with these exact names:

| Label Name | Color | Description |
|-----------|-------|-------------|
| `coderabbit-finding` | 🔴 Red (#E5484D) | Auto-created by CodeRabbit |
| `coderabbit-critical` | 🔴 Red (#E5484D) | Critical security/breaking issues |
| `coderabbit-quality` | 🟡 Yellow (#F5A524) | Code quality improvements |
| `coderabbit-nitpick` | 🔵 Blue (#3B82F6) | Minor formatting/style issues |
| `auto-generated` | 🟣 Purple (#8B5CF6) | Created by automation |
| `ai-generated` | 🟢 Green (#10B981) | Fixed by AI tool |

**Verification**:
```bash
# Labels should appear in Linear label picker
# Test by manually adding label to a test issue
```

**Status**: ⏸️ Awaiting user action

---

### Step 3: Set Environment Variables ⏸️ PENDING

**Time**: 5 minutes
**Owner**: Developer workstation

**Instructions**:

#### Generate Linear API Key
1. Visit https://linear.app/settings/api
2. Click "Create new key"
3. Name: "CodeRabbit Automation"
4. Permissions: Full access (required for GraphQL API)
5. Copy the key (starts with `lin_api_`)

#### Generate GitHub Token
1. Visit https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "CodeRabbit AI Remediation"
4. Scopes:
   - `repo` (full repo access)
   - `workflow` (update workflows)
5. Generate and copy token (starts with `ghp_`)

#### Set Environment Variables
```bash
# Add to ~/.bashrc (or ~/.zshrc if using zsh)
echo 'export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc

# Reload shell configuration
source ~/.bashrc

# Verify
echo $LINEAR_API_KEY  # Should show your key
echo $GITHUB_TOKEN    # Should show your token
```

**Verification**:
```bash
# Test Linear API
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name } }"}' | jq

# Expected: JSON with your Linear user info

# Test GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user | jq .login

# Expected: Your GitHub username
```

**Security Notes**:
- ⚠️ **Never commit these tokens to git**
- ⚠️ **Add to .gitignore if storing in files**
- ⚠️ **Rotate tokens every 90 days**
- ⚠️ **Use GitHub Secrets for Actions** (separate step in Phase 2B)

**Status**: ⏸️ Awaiting user action

---

## 🧪 Testing (PENDING)

### Step 4: Test Manual Script (3 Issues) ⏸️ PENDING

**Time**: 30 minutes
**Owner**: Developer

**Objective**: Validate AI routing logic with 3 different issue types

#### Test Case 1: Critical Security Issue
```bash
# Create test Linear issue:
# Title: "Security: Plain text password in config file"
# Label: coderabbit-critical, security
# Description: "Found password in roles/example/defaults/main.yml"

# Run script
./scripts/fix-linear-issue.sh DEV-XXX

# Expected:
# - Routes to: Claude Code (security reasoning)
# - Creates branch: DEV-XXX-security-...
# - Generates fix (or prompts for manual fix)
# - Creates PR with "Resolves DEV-XXX"
```

**Success Criteria**:
- ✅ Script fetches issue from Linear
- ✅ Routes to correct AI tool (Claude Code)
- ✅ Creates branch with Linear's generated name
- ✅ PR created successfully
- ✅ Linear issue updated

#### Test Case 2: Type Hints Issue
```bash
# Create test Linear issue:
# Title: "Type Hints: Missing Optional[] for None defaults"
# Label: coderabbit-quality, type-hints
# Description: "Missing Optional[str] in function signature"

# Run script
./scripts/fix-linear-issue.sh DEV-YYY

# Expected:
# - Routes to: auto-fix (rules-based)
# - Applies mypy-suggested fixes
# - Creates PR with tests passing
```

**Success Criteria**:
- ✅ Routes to auto-fix tool (not AI)
- ✅ Type hints added correctly
- ✅ Mypy validation passes
- ✅ Tests pass

#### Test Case 3: Code Quality Issue
```bash
# Create test Linear issue:
# Title: "Code Quality: Long function (75 lines)"
# Label: coderabbit-quality, complexity
# Description: "Function exceeds 50 line limit"

# Run script
./scripts/fix-linear-issue.sh DEV-ZZZ

# Expected:
# - Routes to: Cursor (fast refactoring)
# - Prompts for manual refactor
# - Creates PR template
```

**Success Criteria**:
- ✅ Routes to correct tool
- ✅ Script doesn't crash
- ✅ Provides clear next steps

**Test Results Template**:
```
Test Case | AI Tool | Success | Notes
----------|---------|---------|------
Security  | Claude  | ✅/❌   |
Type Hints| auto-fix| ✅/❌   |
Complexity| Cursor  | ✅/❌   |

Overall Success Rate: X/3 (XX%)
```

**Status**: ⏸️ Awaiting Steps 1-3 completion

---

### Step 5: Production Validation (10 Issues) ⏸️ PENDING

**Time**: 2-3 hours over 2 days
**Owner**: DevOps Team

**Objective**: Process 10 real issues from last CodeRabbit review

**Selection Criteria**:
- 5 critical issues (security, FQCN, breaking changes)
- 5 high-priority issues (type hints, error handling, complexity)
- Mix of different file types (.yml, .py, .j2)

**Metrics to Track**:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Success Rate** | > 70% | ___ | ⏸️ |
| **False Positives** | < 20% | ___ | ⏸️ |
| **Time per Issue** | < 5 min | ___ | ⏸️ |
| **Tests Pass** | > 80% | ___ | ⏸️ |
| **Time Saved** | > 10 hr/wk | ___ | ⏸️ |

**Issue Log Template**:
```markdown
| Issue ID | Type | AI Tool | Time | Success | Tests | Notes |
|----------|------|---------|------|---------|-------|-------|
| DEV-101  | Security | Claude | 3 min | ✅ | ✅ | Perfect fix |
| DEV-102  | Type Hints | auto-fix | 2 min | ✅ | ✅ | Automated |
| DEV-103  | FQCN | auto-fix | 2 min | ✅ | ✅ | Automated |
| DEV-104  | Complexity | Cursor | 5 min | ❌ | N/A | Manual needed |
| DEV-105  | Error Handling | Claude | 4 min | ✅ | ⚠️ | Tests failed initially |
| ... | ... | ... | ... | ... | ... | ... |
```

**Status**: ⏸️ Awaiting Step 4 completion

---

## 📊 Phase 2A Decision Gate (Oct 18) ⏸️ PENDING

**Time**: 30 minutes
**Owner**: DevOps Lead + Team

**Objective**: Review Phase 2A metrics and decide on Phase 2B

### Decision Criteria

#### GO to Phase 2B if:
- ✅ AI success rate **> 70%**
- ✅ Nitpick filtering working (< 30 real issues from 70+ nitpicks)
- ✅ No critical false positives
- ✅ Time savings **> 10 hours/week**
- ✅ Team comfortable with automation quality

#### HOLD Phase 2B if:
- ❌ AI success rate **< 60%**
- ❌ False positive rate **> 20%**
- ❌ Routing logic needs significant tuning
- ❌ Security concerns identified
- ❌ Team not confident in automation

#### ABANDON if:
- 🚫 Issue volume decreased (< 20/week) - manual is sufficient
- 🚫 Major bugs in automation
- 🚫 Linear/CodeRabbit integration unstable

### Decision Document Template

```markdown
# Phase 2A → 2B Decision (Oct 18, 2025)

## Metrics Achieved
- Success Rate: ___%
- False Positives: ___%
- Time Saved: ___ hours/week
- Issues Processed: ___
- Cost Savings: $___/week

## Team Feedback
- Strengths: ___
- Weaknesses: ___
- Concerns: ___

## Decision: ✅ GO / ⏸️ HOLD / 🚫 ABANDON

## Reasoning:
___

## Next Steps:
___

**Decided By**: ___
**Date**: October 18, 2025
```

**Status**: ⏸️ Awaiting Step 5 completion

---

## 📝 Post-Deployment (PENDING)

### Documentation Updates ⏸️ PENDING

**After successful Phase 2A validation**:

- [ ] Update `docs/ci-cd/CODERABBIT-AUTOMATION.md` with:
  - Actual success rates
  - Common issues encountered
  - Lessons learned
  - Optimization tips

- [ ] Create `docs/ci-cd/PHASE-2A-RESULTS.md`:
  - Final metrics
  - Issue log (anonymized if needed)
  - Team feedback
  - Recommendations for Phase 2B

- [ ] Update `docs/Delivery-Enhancements/TASK-TRACKER.md`:
  - Mark TASK-035A complete (CodeRabbit → Linear integration)
  - Mark TASK-035B complete (AI fix routing script)

**Status**: ⏸️ Awaiting Phase 2A completion

---

## 🚨 Troubleshooting

### Issue: Linear API Key Not Working

**Symptom**: `curl` test returns 401 Unauthorized

**Solutions**:
1. Regenerate API key (may have been invalidated)
2. Check for extra spaces in `.bashrc`
3. Verify key starts with `lin_api_`
4. Try in new terminal (reload environment)

### Issue: Script Can't Find `jq`

**Symptom**: `command not found: jq`

**Solution**:
```bash
sudo apt update
sudo apt install -y jq
```

### Issue: GitHub Token Permissions Denied

**Symptom**: `gh pr create` returns 403 Forbidden

**Solutions**:
1. Regenerate token with `repo` and `workflow` scopes
2. Authenticate GitHub CLI: `gh auth login`
3. Use token when prompted

### Issue: CodeRabbit Not Creating Linear Issues

**Symptom**: PR reviewed but no Linear issues created

**Checks**:
1. ✅ Linear integration enabled in CodeRabbit settings?
2. ✅ `.coderabbit.yaml` committed to repo root?
3. ✅ Issue severity is critical or high?
4. ✅ Linear labels exist?

**Solution**: Check CodeRabbit logs in PR comments for errors

---

## 📞 Support Contacts

**Technical Issues**:
- Script bugs: Check `scripts/fix-linear-issue.sh` comments
- Configuration: See `docs/ci-cd/CODERABBIT-AUTOMATION.md`

**Access Issues**:
- Linear admin: [Your Linear Admin]
- CodeRabbit account: [Your CodeRabbit Admin]
- GitHub org admin: [Your GitHub Admin]

**Escalation**:
- DevOps Lead: [Name/Contact]
- Project Manager: [Name/Contact]

---

## 📈 Progress Tracking

**Last Updated**: October 11, 2025

| Step | Status | Owner | ETA | Actual |
|------|--------|-------|-----|--------|
| 1. Enable Linear Integration | ⏸️ Pending | User | Oct 11 | ___ |
| 2. Create Linear Labels | ⏸️ Pending | User | Oct 11 | ___ |
| 3. Set Environment Variables | ⏸️ Pending | User | Oct 11 | ___ |
| 4. Test Script (3 issues) | ⏸️ Pending | Developer | Oct 14 | ___ |
| 5. Validation (10 issues) | ⏸️ Pending | Team | Oct 15-17 | ___ |
| 6. Decision Gate | ⏸️ Pending | Lead | Oct 18 | ___ |

**Overall Phase 2A Progress**: 2/6 steps complete (33%)

**Blockers**: None (awaiting user actions on Steps 1-3)

---

**Next Milestone**: Phase 2B (GitHub Actions) - Week of Oct 21, 2025

**Related Documents**:
- [CODERABBIT-AUTOMATION.md](CODERABBIT-AUTOMATION.md) - Complete guide
- [CODERABBIT-ACCELERATED-ROADMAP.md](CODERABBIT-ACCELERATED-ROADMAP.md) - Full timeline
- [CODERABBIT-COMPARISON.md](CODERABBIT-COMPARISON.md) - Phase comparison

---

**Status**: 🚀 ACTIVE - Ready for user actions (Steps 1-3)
**Last Updated**: October 11, 2025, 4:20 PM
**Next Update**: After Step 3 completion
