# CodeRabbit CLI Integration - HX-Citadel

Complete guide to using CodeRabbit CLI in our automation pipeline.

## Overview

CodeRabbit CLI provides **instant code review** directly in your terminal, eliminating delays from PR-based reviews. We've integrated it into our "Log → Assign → Fix" automation pipeline.

## Quick Start

### Local Development

```bash
# Review your uncommitted changes
coderabbit --plain

# Review against specific base branch
coderabbit --plain --base develop

# Get output optimized for AI agents
coderabbit --prompt-only
```

### With Automatic Issue Creation

```bash
# Run review and create GitHub issues automatically
.github/scripts/review-and-create-issues.sh . <pr_number>

# Auto-detect PR number
.github/scripts/review-and-create-issues.sh
```

## Integration Points

### 1. Local Development (Manual)

**Use case**: Get instant feedback while coding

```bash
# Make changes
git add .

# Run review before commit
coderabbit --plain

# See findings, fix issues, then commit
git commit -m "fix: address code review findings"
```

### 2. Pre-commit Hook (Automated)

**Use case**: Block commits with critical issues

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Run CodeRabbit review before allowing commit

echo "🤖 Running CodeRabbit review..."
coderabbit --plain --type uncommitted > /tmp/cr-review.txt

if grep -q "CRITICAL" /tmp/cr-review.txt; then
    echo "❌ CRITICAL issues found - commit blocked"
    cat /tmp/cr-review.txt
    exit 1
fi

echo "✅ No critical issues - proceeding with commit"
```

### 3. CI Workflow (Automated)

**Use case**: Auto-review on push, create GitHub issues

Workflow: `.github/workflows/cli-review-on-push.yml`

**Triggers on**:
- Push to feature/bugfix branches
- Push to sprint branches
- Manual workflow dispatch

**What it does**:
1. Runs `coderabbit --plain --base main`
2. Parses findings
3. Creates GitHub issues automatically
4. Comments on PR with summary
5. Uploads review as artifact

### 4. AI Agent Integration (You + Claude)

**Use case**: Get CodeRabbit analysis, Claude implements fixes

```bash
# Get findings optimized for AI
coderabbit --prompt-only > findings.txt

# Share with Claude
cat findings.txt
# Claude reads, understands, implements fixes
```

## Automated Issue Creation Pipeline

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Developer Pushes → CLI Review → Parse Findings →       │
│  Create GitHub Issues → Link to PR → Notify Team        │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **CodeRabbit CLI** - Reviews code, outputs findings
2. **Parser Script** - `.github/scripts/parse-review-create-issues.py`
3. **Wrapper Script** - `.github/scripts/review-and-create-issues.sh`
4. **CI Workflow** - `.github/workflows/cli-review-on-push.yml`

### Issue Creation Rules

**Creates issues for**:
- ✅ CRITICAL severity findings
- ✅ MAJOR severity findings
- ✅ HIGH priority findings

**Skips**:
- ⏭️ Minor/low severity findings
- ⏭️ Style/formatting suggestions
- ⏭️ Positive observations

**Labels applied**:
- `code-review` - From automated review
- `automated` - Auto-created by workflow
- `critical` or `major` - Based on severity
- `high-priority` - For high severity issues

## Review Modes

### Interactive Mode (Default)

```bash
coderabbit
```

**Best for**: Manual review with browsable interface

### Plain Text Mode

```bash
coderabbit --plain
```

**Best for**: Parsing, logging, automation

### Prompt-Only Mode

```bash
coderabbit --prompt-only
```

**Best for**: AI agents, minimal output, token efficiency

## Configuration

### Authentication

```bash
# Login to enable learnings and context
coderabbit auth login

# Or use short alias
cr auth login
```

### Custom Instructions

Pass additional context files:

```bash
coderabbit --plain --config .cursorrules --config CLAUDE.md
```

Our project automatically detects:
- `.cursorrules`
- `CLAUDE.md`
- `.coderabbit.yaml`

### Base Branch

Specify comparison branch:

```bash
# Compare against develop
coderabbit --base develop

# Compare against specific commit
coderabbit --base-commit abc123
```

## Workflow Examples

### Scenario 1: Feature Development

```bash
# 1. Start feature
git checkout -b feature/new-api

# 2. Make changes
# ... code, code, code ...

# 3. Quick review before commit
coderabbit --plain | tee review.txt

# 4. Address findings
# ... fix, fix, fix ...

# 5. Commit
git commit -m "feat: add new API endpoint"

# 6. Push (triggers CI review)
git push origin feature/new-api

# 7. CI automatically:
#    - Runs coderabbit review
#    - Creates GitHub issues for findings
#    - Comments on PR
```

### Scenario 2: Pre-commit Check

```bash
# Before every commit
git add .
coderabbit --plain

# If OK, commit
git commit -m "..."

# If issues found, fix first
# ... address findings ...
git commit -m "..."
```

### Scenario 3: CI Integration

```yaml
# .github/workflows/custom.yml
- name: CodeRabbit Review
  run: |
    coderabbit --plain > review.txt
    python3 .github/scripts/parse-review-create-issues.py \
      review.txt ${{ github.event.pull_request.number }} ${{ secrets.GITHUB_TOKEN }}
```

## Differences: CLI vs PR Reviews

### CLI Reviews
- ✅ **Instant feedback** (seconds)
- ✅ **Local changes** (uncommitted files)
- ✅ **Immediate iteration** (fix and re-review)
- ✅ **Learnings-powered** (paid users)
- ⏭️ No chat, docstrings, or unit test generation

### PR Reviews  
- ✅ **Team collaboration** (comments, discussions)
- ✅ **Full repository context**
- ✅ **Chat and docstring generation**
- ✅ **Historical tracking**
- ⏱️ Requires PR creation (minutes delay)

## Troubleshooting

### Issue: "coderabbit: command not found"

```bash
# Reinstall
curl -fsSL https://cli.coderabbit.ai/install.sh | sh

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

### Issue: "Authentication required"

```bash
# Login
coderabbit auth login

# Or set token via environment
export CODERABBIT_TOKEN="your-token"
```

### Issue: "No findings in review"

This is good! It means no critical issues were detected.

```bash
# Verify review ran
coderabbit --plain | tee review.log

# Check output
cat review.log
```

### Issue: "Issues not created automatically"

Check:
1. ✅ Is `GITHUB_TOKEN` set?
2. ✅ Did review have CRITICAL/MAJOR findings?
3. ✅ Is workflow enabled?
4. ✅ Are you on a feature branch?

```bash
# Run manually
python3 .github/scripts/parse-review-create-issues.py \
  review.txt <pr_number> $GITHUB_TOKEN
```

## Best Practices

### DO ✅
- Run `coderabbit --plain` before every commit
- Review findings while code is fresh
- Use `--base` for accurate diffs
- Authenticate for learnings-powered reviews
- Let CI create issues automatically

### DON'T ❌
- Ignore CRITICAL findings
- Skip reviews on "small changes"
- Commit without reviewing
- Disable workflows without reason
- Create duplicate manual issues

## Rate Limits

- **Free tier**: Limited daily reviews
- **Paid tier**: Higher limits + learnings
- **Enterprise**: Custom limits

See [pricing](https://coderabbit.ai/pricing) for details.

## Support

- **CLI Issues**: [GitHub Issues](https://github.com/hanax-ai/hx-citadel-ansible/issues)
- **CodeRabbit Support**: sales@coderabbit.ai
- **Internal**: #devops channel

---

**Last Updated**: October 12, 2025  
**Status**: ✅ Fully operational  
**Automation**: Complete "Log → Assign → Fix" pipeline active
