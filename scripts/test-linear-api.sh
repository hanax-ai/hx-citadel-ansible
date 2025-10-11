#!/bin/bash
###############################################################################
# Linear API Test Script
# Tests Linear API authentication and finds your team key
###############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Linear API Connection Test        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Check for API key
if [[ -z "${LINEAR_API_KEY:-}" ]]; then
    echo -e "${RED}❌ ERROR: LINEAR_API_KEY not set${NC}"
    echo
    echo "Please export your Linear API key:"
    echo "  export LINEAR_API_KEY=\"lin_api_YOUR_KEY_HERE\""
    echo
    echo "Get your key from: https://linear.app/settings/api"
    exit 1
fi

echo -e "${YELLOW}Testing authentication...${NC}"

# Test 1: Viewer query (basic auth test)
RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"query": "{ viewer { id name email admin } }"}')

# Check for errors
if echo "$RESPONSE" | jq -e '.errors' >/dev/null 2>&1; then
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.errors[0].message')
    echo -e "${RED}❌ Authentication FAILED${NC}"
    echo -e "${RED}Error: $ERROR_MSG${NC}"
    echo
    echo "Possible causes:"
    echo "  1. API key is invalid or expired"
    echo "  2. API key doesn't have required permissions"
    echo "  3. Workspace access issue"
    echo
    echo "Solution:"
    echo "  1. Go to https://linear.app/settings/api"
    echo "  2. Delete the old key"
    echo "  3. Create NEW key with 'Full access' or 'Read/Write' permissions"
    echo "  4. Export the new key: export LINEAR_API_KEY=\"lin_api_...\""
    exit 1
fi

# Success!
USER_NAME=$(echo "$RESPONSE" | jq -r '.data.viewer.name')
USER_EMAIL=$(echo "$RESPONSE" | jq -r '.data.viewer.email')
IS_ADMIN=$(echo "$RESPONSE" | jq -r '.data.viewer.admin')

echo -e "${GREEN}✅ Authentication SUCCESS${NC}"
echo -e "${GREEN}   User: $USER_NAME ($USER_EMAIL)${NC}"
echo -e "${GREEN}   Admin: $IS_ADMIN${NC}"
echo

# Test 2: Get teams
echo -e "${YELLOW}Fetching Linear teams...${NC}"

TEAMS_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"query": "{ teams { nodes { id key name } } }"}')

# Check for errors
if echo "$TEAMS_RESPONSE" | jq -e '.errors' >/dev/null 2>&1; then
    echo -e "${RED}❌ Failed to fetch teams${NC}"
    echo "$TEAMS_RESPONSE" | jq -r '.errors[0].message'
    exit 1
fi

# Display teams
TEAM_COUNT=$(echo "$TEAMS_RESPONSE" | jq -r '.data.teams.nodes | length')

if [[ "$TEAM_COUNT" -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No teams found${NC}"
    echo "You may need to be added to a team in Linear"
else
    echo -e "${GREEN}✅ Found $TEAM_COUNT team(s):${NC}"
    echo
    echo "$TEAMS_RESPONSE" | jq -r '.data.teams.nodes[] | "  • \(.key) - \(.name)"'
    echo
    echo -e "${BLUE}ℹ️  Use these team keys to fetch issues:${NC}"
    echo "$TEAMS_RESPONSE" | jq -r '.data.teams.nodes[] | "  ./scripts/fetch-linear-issue.sh \"\(.key)-123\""'
fi

echo
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     All Tests PASSED ✅                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo
echo "Next steps:"
echo "  1. Note your team key(s) from above"
echo "  2. Find a real Linear issue ID (e.g., ENG-123)"
echo "  3. Test the fetch script:"
echo "     ./scripts/fetch-linear-issue.sh \"TEAM-123\""
echo
