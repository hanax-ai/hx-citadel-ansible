#!/bin/bash
#
# Automated Issue Assignment and Management
# 
# Purpose: Pull open issues, assign to appropriate agents (Devin, agent0, etc.)
#
# Usage: ./assign-issues.sh [--dry-run]

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

REPO="hanax-ai/hx-citadel-ansible"
API_BASE="https://api.github.com/repos/$REPO"

# GitHub token from environment
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "❌ GITHUB_TOKEN environment variable required"
    exit 1
fi

# Fetch all open issues
echo "📥 Fetching open issues from $REPO..."
ISSUES=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "$API_BASE/issues?state=open&per_page=100")

# Parse issues into assignable categories
TOTAL_ISSUES=$(echo "$ISSUES" | jq '. | length')
UNASSIGNED=$(echo "$ISSUES" | jq '[.[] | select(.assignee == null)] | length')
ASSIGNED_TO_DEVIN=$(echo "$ISSUES" | jq '[.[] | select(.assignee.login == "devin")] | length')

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   📊 ISSUE STATISTICS"
echo "═══════════════════════════════════════════════════════════"
echo "Total Open Issues: $TOTAL_ISSUES"
echo "Unassigned Issues: $UNASSIGNED"
echo "Assigned to Devin: $ASSIGNED_TO_DEVIN"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Issue Assignment Rules
# 
# Devin (Backend/Infrastructure AI):
# - Ansible role creation
# - Docker/deployment issues
# - Backend infrastructure
# - Security vault issues
#
# Agent0/Claude (Code Quality/Testing AI):
# - Testing issues
# - Linting/code quality
# - Documentation
# - Frontend issues

echo "🤖 Applying assignment rules..."

# Get unassigned issues with specific labels
BACKEND_ISSUES=$(echo "$ISSUES" | jq -r '.[] | select(.assignee == null) | select(.labels[]?.name | contains("critical") or contains("ansible") or contains("docker") or contains("infrastructure")) | .number')

TESTING_ISSUES=$(echo "$ISSUES" | jq -r '.[] | select(.assignee == null) | select(.title | contains("test") or contains("Test") or contains("integration")) | .number')

LINTING_ISSUES=$(echo "$ISSUES" | jq -r '.[] | select(.assignee == null) | select(.title | contains("lint") or contains("ansible-lint")) | .number')

# Assign backend/infrastructure issues to Devin
for issue in $BACKEND_ISSUES; do
    title=$(echo "$ISSUES" | jq -r ".[] | select(.number == $issue) | .title")
    echo "  → Issue #$issue: $title → Devin (Backend/Infrastructure)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        curl -s -X PATCH \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "$API_BASE/issues/$issue" \
            -d '{"assignees":["devin"]}' > /dev/null
    fi
done

# Assign testing issues to agent0
for issue in $TESTING_ISSUES; do
    title=$(echo "$ISSUES" | jq -r ".[] | select(.number == $issue) | .title")
    echo "  → Issue #$issue: $title → agent0 (Testing/QA)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        curl -s -X PATCH \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "$API_BASE/issues/$issue" \
            -d '{"assignees":["agent0"]}' > /dev/null
    fi
done

# Assign linting issues to agent0
for issue in $LINTING_ISSUES; do
    title=$(echo "$ISSUES" | jq -r ".[] | select(.number == $issue) | .title")
    echo "  → Issue #$issue: $title → agent0 (Code Quality)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        curl -s -X PATCH \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "$API_BASE/issues/$issue" \
            -d '{"assignees":["agent0"]}' > /dev/null
    fi
done

echo ""
echo "✅ Issue assignment complete!"

