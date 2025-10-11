#!/bin/bash
###############################################################################
# Auto-Fix Type Hints Script
#
# Purpose: Automatically add missing type hints to Python files
# Usage: ./auto-fix-types.sh [file_or_directory]
#
# Phase 2A: Basic implementation using mypy suggestions
# Phase 2B: Enhanced with AI-powered type inference
###############################################################################

set -euo pipefail

# Configuration
TARGET="${1:-.}"
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Auto-Fix Type Hints Tool              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Phase 2A: Use mypy to identify missing type hints
###############################################################################

echo -e "${YELLOW}⚠️  Phase 2A: Limited Implementation${NC}"
echo -e "${YELLOW}This script identifies files with missing type hints${NC}"
echo -e "${YELLOW}but requires manual/AI-assisted fix for now.${NC}"
echo ""

# Run mypy and capture output
echo -e "${BLUE}Running mypy on: $TARGET${NC}"

MYPY_OUTPUT=$(mypy "$TARGET" --show-error-codes --no-error-summary 2>&1 || true)

# Parse mypy output for type hint issues
FILES_WITH_ISSUES=$(echo "$MYPY_OUTPUT" | grep -oP '^[^:]+(?=:.*\[.*\])' | sort -u || true)

if [ -z "$FILES_WITH_ISSUES" ]; then
    echo -e "${GREEN}✅ No type hint issues found!${NC}"
    exit 0
fi

echo -e "${YELLOW}Found type hint issues in:${NC}"
echo "$FILES_WITH_ISSUES" | while read -r file; do
    echo -e "${YELLOW}  - $file${NC}"
done
echo ""

###############################################################################
# Phase 2A: Generate fix suggestions (not automated yet)
###############################################################################

echo -e "${BLUE}Generating fix suggestions...${NC}"
echo ""

echo "$FILES_WITH_ISSUES" | while read -r file; do
    echo -e "${YELLOW}File: $file${NC}"
    
    # Extract specific errors for this file
    ERRORS=$(echo "$MYPY_OUTPUT" | grep "^$file:" | head -5)
    
    echo "$ERRORS" | while read -r error; do
        echo -e "  ${RED}→${NC} $error"
    done
    
    echo ""
done

###############################################################################
# Phase 2B: AI-Powered Auto-Fix (TODO)
###############################################################################

echo -e "${YELLOW}╔════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Phase 2B: AI-Powered Auto-Fix NOT YET READY   ║${NC}"
echo -e "${YELLOW}╠════════════════════════════════════════════════╣${NC}"
echo -e "${YELLOW}║  This script currently IDENTIFIES issues but   ║${NC}"
echo -e "${YELLOW}║  does NOT automatically fix them.              ║${NC}"
echo -e "${YELLOW}║                                                ║${NC}"
echo -e "${YELLOW}║  Options for fixing:                           ║${NC}"
echo -e "${YELLOW}║  1. Manual fix (recommended for Phase 2A)      ║${NC}"
echo -e "${YELLOW}║  2. Use Claude Code / Cursor (AI-assisted)     ║${NC}"
echo -e "${YELLOW}║  3. Wait for Phase 2B full automation          ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Count issues
ISSUE_COUNT=$(echo "$FILES_WITH_ISSUES" | wc -l)

echo -e "${BLUE}Summary:${NC}"
echo -e "  Files with type hint issues: ${RED}$ISSUE_COUNT${NC}"
echo -e "  Action required: ${YELLOW}Manual review and fix${NC}"
echo ""

# Exit with error code to indicate issues found
exit 1

