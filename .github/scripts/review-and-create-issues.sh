#!/bin/bash
# Enhanced workflow: Run CodeRabbit CLI → Parse results → Create GitHub issues immediately

set -e

REPO_DIR="${1:-.}"
PR_NUMBER="${2:-}"
BASE_BRANCH="${3:-main}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo "═══════════════════════════════════════════════════════════"
echo "   🤖 CodeRabbit CLI → GitHub Issues Pipeline"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Repository: $REPO_DIR"
echo "Base Branch: $BASE_BRANCH"
echo "PR Number: ${PR_NUMBER:-Auto-detect}"
echo ""

cd "$REPO_DIR"

# Step 1: Run CodeRabbit review
echo "📝 Step 1: Running CodeRabbit review..."
echo "Command: coderabbit --plain --base $BASE_BRANCH"
echo ""

# Run review and save output
REVIEW_OUTPUT="/tmp/coderabbit-review-$(date +%s).txt"
coderabbit --plain --base "$BASE_BRANCH" > "$REVIEW_OUTPUT" 2>&1 || {
    echo "⚠️  CodeRabbit review completed with warnings"
}

echo "✅ Review complete. Output saved to: $REVIEW_OUTPUT"
echo ""

# Step 2: Check if there are findings
if ! grep -q "CRITICAL\|MAJOR\|HIGH" "$REVIEW_OUTPUT" 2>/dev/null; then
    echo "✅ No critical issues found! 🎉"
    echo ""
    cat "$REVIEW_OUTPUT"
    exit 0
fi

echo "📊 Findings detected in review"
echo ""

# Step 3: Auto-detect PR number if not provided
if [ -z "$PR_NUMBER" ]; then
    echo "🔍 Auto-detecting PR number..."
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    if [ "$CURRENT_BRANCH" == "main" ] || [ "$CURRENT_BRANCH" == "master" ]; then
        echo "⚠️  On main branch - cannot auto-detect PR"
        echo "   Please provide PR number as second argument"
        exit 1
    fi
    
    # Try to find PR for current branch
    if [ -n "$GITHUB_TOKEN" ]; then
        PR_NUMBER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.github.com/repos/hanax-ai/hx-citadel-ansible/pulls?head=hanax-ai:$CURRENT_BRANCH&state=open" \
            | jq -r '.[0].number // empty')
    fi
    
    if [ -z "$PR_NUMBER" ]; then
        echo "⚠️  Could not auto-detect PR number"
        echo "   Using branch name as reference: $CURRENT_BRANCH"
        PR_NUMBER="$CURRENT_BRANCH"
    else
        echo "✅ Found PR #$PR_NUMBER"
    fi
fi

echo ""

# Step 4: Parse review and create GitHub issues
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set - cannot create issues"
    echo "   Review results saved to: $REVIEW_OUTPUT"
    echo ""
    echo "To create issues manually, run:"
    echo "  python3 .github/scripts/parse-review-create-issues.py \\"
    echo "    $REVIEW_OUTPUT $PR_NUMBER \$GITHUB_TOKEN"
    exit 0
fi

echo "🚀 Step 2: Creating GitHub issues from findings..."
echo ""

python3 .github/scripts/parse-review-create-issues.py \
    "$REVIEW_OUTPUT" \
    "$PR_NUMBER" \
    "$GITHUB_TOKEN"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   ✅ Pipeline Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Review output: $REVIEW_OUTPUT"
echo "Check GitHub issues: https://github.com/hanax-ai/hx-citadel-ansible/issues"
echo ""

