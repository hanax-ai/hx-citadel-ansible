#!/bin/bash
###############################################################################
# Fetch Linear Issue Details
#
# Purpose: Fetch issue details from Linear API, handling both human-friendly
#          identifiers (DEV-123) and global IDs
#
# Usage: ./fetch-linear-issue.sh <issue-id>
#
# Outputs: JSON with issue details to stdout
###############################################################################

set -euo pipefail

ISSUE_ID="${1:-}"
LINEAR_API_KEY="${LINEAR_API_KEY:-}"

if [[ -z "$ISSUE_ID" ]]; then
    echo "{\"error\": \"Missing issue ID\"}" >&2
    exit 1
fi

if [[ -z "$LINEAR_API_KEY" ]]; then
    echo "{\"error\": \"LINEAR_API_KEY not set\"}" >&2
    exit 1
fi

# Parse human-friendly identifier (e.g., DEV-123)
if [[ "$ISSUE_ID" =~ ^([A-Z]+)-([0-9]+)$ ]]; then
    TEAM_KEY="${BASH_REMATCH[1]}"
    ISSUE_NUMBER="${BASH_REMATCH[2]}"

    # Step 1: Get team ID from team key
    TEAM_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"{ teams(filter: { key: { eq: \\\"$TEAM_KEY\\\" } }) { nodes { id key } } }\"}")

    TEAM_ID=$(echo "$TEAM_RESPONSE" | jq -r '.data.teams.nodes[0].id')

    if [[ -z "$TEAM_ID" || "$TEAM_ID" == "null" ]]; then
        echo "{\"error\": \"Team not found: $TEAM_KEY\"}" >&2
        exit 1
    fi

    # Step 2: Get issue using team filter
    # Use the simpler 'issues' query with filters instead of parameterized query
    ISSUE_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"{ issues(filter: { team: { key: { eq: \\\"$TEAM_KEY\\\" } }, number: { eq: $ISSUE_NUMBER } }) { nodes { id identifier title description priority branchName state { name } labels { nodes { name } } } } }\"}")

    # Extract the first (and only) issue from the results
    echo "$ISSUE_RESPONSE" | jq '.data.issues.nodes[0]'

else
    # Fallback: treat as global ID
    ISSUE_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"{ issue(id: \\\"$ISSUE_ID\\\") { id identifier title description priority branchName state { name } labels { nodes { name } } } }\"}")

    echo "$ISSUE_RESPONSE" | jq '.data.issue'
fi
