#!/bin/bash
###############################################################################
# AI-Assisted Linear Issue Remediation Script
#
# Purpose: Automate the workflow for fixing CodeRabbit findings tracked in Linear
# Usage: ./fix-linear-issue.sh <linear-issue-id>
#
# Workflow:
# 1. Fetch Linear issue details via GraphQL API
# 2. Extract CodeRabbit finding context
# 3. Route to appropriate AI tool (Claude Code, Cursor, or auto-fix script)
# 4. Create fix branch and auto-commit
# 5. Create PR with CodeRabbit re-review
#
# Requirements:
# - LINEAR_API_KEY environment variable
# - GITHUB_TOKEN for PR creation
# - AI tool CLI (claude-code or cursor)
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LINEAR_API_KEY="${LINEAR_API_KEY:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
ISSUE_ID="${1:-}"

# Validation
if [[ -z "$ISSUE_ID" ]]; then
    echo -e "${RED}Error: Missing Linear issue ID${NC}"
    echo "Usage: $0 <linear-issue-id>"
    exit 1
fi

if [[ -z "$LINEAR_API_KEY" ]]; then
    echo -e "${RED}Error: LINEAR_API_KEY environment variable not set${NC}"
    exit 1
fi

###############################################################################
# Function: Fetch Linear Issue Details
###############################################################################
fetch_linear_issue() {
    local issue_id="$1"

    echo -e "${BLUE}📥 Fetching Linear issue: $issue_id${NC}"

    # Use the fetch-linear-issue.sh helper script
    local script_dir="$(dirname "$(readlink -f "$0")")"
    local issue_json=$("$script_dir/fetch-linear-issue.sh" "$issue_id")

    # Check for errors
    if echo "$issue_json" | jq -e '.error' >/dev/null 2>&1; then
        echo -e "${RED}Error: $(echo "$issue_json" | jq -r '.error')${NC}"
        exit 1
    fi

    # Wrap in GraphQL response format for compatibility with existing code
    echo "{\"data\": {\"issue\": $issue_json}}"
}

###############################################################################
# Function: Determine AI Tool Based on Issue Type
###############################################################################
determine_ai_tool() {
    local issue_labels="$1"
    local issue_priority="$2"

    # Check labels for routing
    if echo "$issue_labels" | grep -q "coderabbit-critical\|security"; then
        echo "claude-code"  # Complex reasoning needed
    elif echo "$issue_labels" | grep -q "coderabbit-quality\|refactor"; then
        echo "cursor"  # Fast refactoring
    elif echo "$issue_labels" | grep -q "type-hints\|mypy"; then
        echo "auto-fix"  # Automated script
    elif echo "$issue_labels" | grep -q "tests\|coverage"; then
        echo "claude-code"  # Needs business logic understanding
    elif echo "$issue_labels" | grep -q "formatting\|linting"; then
        echo "pre-commit"  # Fully automated
    else
        echo "claude-code"  # Default to Claude for unknowns
    fi
}

###############################################################################
# Function: Create Fix Branch
###############################################################################
create_fix_branch() {
    local issue_identifier="$1"
    local branch_name="fix/${issue_identifier,,}"  # Lowercase

    echo -e "${BLUE}🌿 Creating fix branch: $branch_name${NC}"

    # Ensure on main/master
    git checkout main 2>/dev/null || git checkout master
    git pull origin main 2>/dev/null || git pull origin master

    # Create and checkout new branch
    git checkout -b "$branch_name"

    echo "$branch_name"
}

###############################################################################
# Function: Route to AI Tool
###############################################################################
route_to_ai() {
    local tool="$1"
    local issue_title="$2"
    local issue_description="$3"

    case "$tool" in
        claude-code)
            echo -e "${GREEN}🤖 Routing to Claude Code${NC}"
            # Use Claude Code CLI (if available) or manual prompt
            echo "Prompt: Fix the following issue:"
            echo "$issue_title"
            echo "$issue_description"
            # TODO: Integrate with Claude Code API when available
            ;;
        cursor)
            echo -e "${GREEN}⚡ Routing to Cursor${NC}"
            # Use Cursor CLI or API
            # TODO: Integrate with Cursor
            ;;
        auto-fix)
            echo -e "${GREEN}🔧 Running automated fix script${NC}"
            # Run mypy or linting auto-fix
            if echo "$issue_description" | grep -q "type hint"; then
                # Run type hints auto-fix
                "$REPO_ROOT/scripts/auto-fix-types.sh"
            fi
            ;;
        pre-commit)
            echo -e "${GREEN}🎨 Running pre-commit hooks${NC}"
            pre-commit run --all-files
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown tool: $tool. Manual fix required.${NC}"
            ;;
    esac
}

###############################################################################
# Function: Create Pull Request
###############################################################################
create_pull_request() {
    local issue_identifier="$1"
    local issue_title="$2"
    local branch_name="$3"

    echo -e "${BLUE}📝 Creating Pull Request${NC}"

    # Push branch
    git push -u origin "$branch_name"

    # Create PR using GitHub CLI
    if command -v gh &> /dev/null; then
        gh pr create \
            --title "Fix $issue_identifier: $issue_title" \
            --body "Fixes Linear issue $issue_identifier

**CodeRabbit Finding**: $issue_title

**Changes**:
- Auto-generated fix using AI remediation workflow

**Testing**:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] CodeRabbit re-review approved

🤖 Generated by AI Issue Remediation Script" \
            --label "coderabbit-fix,ai-generated"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not installed. Create PR manually.${NC}"
        echo "Branch: $branch_name"
    fi
}

###############################################################################
# Main Execution
###############################################################################
main() {
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  AI-Assisted Issue Remediation Tool   ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo ""

    # Step 1: Fetch issue details
    local issue_data=$(fetch_linear_issue "$ISSUE_ID")

    # Parse issue details (using jq)
    local issue_identifier=$(echo "$issue_data" | jq -r '.data.issue.identifier')
    local issue_title=$(echo "$issue_data" | jq -r '.data.issue.title')
    local issue_description=$(echo "$issue_data" | jq -r '.data.issue.description')
    local issue_priority=$(echo "$issue_data" | jq -r '.data.issue.priority')
    local issue_labels=$(echo "$issue_data" | jq -r '.data.issue.labels.nodes[].name' | tr '\n' ',')

    echo -e "${BLUE}Issue: $issue_identifier - $issue_title${NC}"
    echo -e "${BLUE}Priority: $issue_priority${NC}"
    echo -e "${BLUE}Labels: $issue_labels${NC}"
    echo ""

    # Step 2: Determine AI tool
    local ai_tool=$(determine_ai_tool "$issue_labels" "$issue_priority")
    echo -e "${GREEN}Selected AI Tool: $ai_tool${NC}"
    echo ""

    # Step 3: Create fix branch
    local branch_name=$(create_fix_branch "$issue_identifier")
    echo ""

    # Step 4: Route to AI for remediation
    route_to_ai "$ai_tool" "$issue_title" "$issue_description"
    echo ""

    # Step 5: Commit changes (if any)
    if [[ -n "$(git status --porcelain)" ]]; then
        echo -e "${BLUE}📦 Committing changes${NC}"
        git add .
        git commit -m "fix($issue_identifier): $issue_title

AI-generated fix for CodeRabbit finding.

🤖 Generated with AI Issue Remediation Script"
        echo ""

        # Step 6: Create PR
        create_pull_request "$issue_identifier" "$issue_title" "$branch_name"
    else
        echo -e "${YELLOW}⚠️  No changes to commit. Fix may require manual intervention.${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ Remediation workflow complete!${NC}"
}

# Execute main function
main
