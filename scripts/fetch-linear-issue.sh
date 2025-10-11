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

    # Validate ISSUE_NUMBER is a valid integer
    if ! [[ "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
        echo "{\"error\": \"Invalid issue number: $ISSUE_NUMBER\"}" >&2
        exit 1
    fi

    # Step 1: Get team ID from team key using GraphQL variables
    TEAM_QUERY='query GetTeam($teamKey: String!) { teams(filter: { key: { eq: $teamKey } }) { nodes { id key } } }'
    TEAM_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -nc --arg query "$TEAM_QUERY" --arg teamKey "$TEAM_KEY" '{query: $query, variables: {teamKey: $teamKey}}')")

    TEAM_ID=$(echo "$TEAM_RESPONSE" | jq -r '.data.teams.nodes[0].id')

    if [[ -z "$TEAM_ID" || "$TEAM_ID" == "null" ]]; then
        echo "{\"error\": \"Team not found: $TEAM_KEY\"}" >&2
        exit 1
    fi

    # Step 2: Get issue using team filter with GraphQL variables
    ISSUE_QUERY='query GetIssue($teamKey: String!, $issueNumber: Int!) { issues(filter: { team: { key: { eq: $teamKey } }, number: { eq: $issueNumber } }) { nodes { id identifier title description priority branchName state { name } labels { nodes { name } } } } }'
    ISSUE_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -nc --arg query "$ISSUE_QUERY" --arg teamKey "$TEAM_KEY" --argjson issueNumber "$ISSUE_NUMBER" '{query: $query, variables: {teamKey: $teamKey, issueNumber: $issueNumber}}')")

    # Extract the first (and only) issue from the results
    echo "$ISSUE_RESPONSE" | jq '.data.issues.nodes[0]'

else
    # Fallback: treat as global ID using GraphQL variables
    ISSUE_BY_ID_QUERY='query GetIssueById($issueId: String!) { issue(id: $issueId) { id identifier title description priority branchName state { name } labels { nodes { name } } } }'
    ISSUE_RESPONSE=$(curl -s -X POST https://api.linear.app/graphql \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -nc --arg query "$ISSUE_BY_ID_QUERY" --arg issueId "$ISSUE_ID" '{query: $query, variables: {issueId: $issueId}}')")

    echo "$ISSUE_RESPONSE" | jq '.data.issue'
fi
