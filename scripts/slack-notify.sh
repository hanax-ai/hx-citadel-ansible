#!/bin/bash
###############################################################################
# Slack Notification Helper
#
# Purpose: Send formatted notifications to Slack with attachments and fields
# Usage: ./slack-notify.sh <webhook_url> <message> <color> [field_title field_value field_short...]
#
# Parameters:
#   webhook_url - Slack incoming webhook URL
#   message     - Main message text
#   color       - Attachment color (hex code: #36a64f for green, #ff0000 for red)
#   fields      - Optional field triplets: title, value, short (true/false)
#
# Example:
#   ./slack-notify.sh "$WEBHOOK" "Deployment Started" "#36a64f" \
#     "Environment" "Production" "true" \
#     "Version" "v1.2.3" "true"
#
# SOLID Principles:
# - Single Responsibility: Only handles Slack notifications
# - Open/Closed: Extensible via field parameters
# - Dependency Inversion: Accepts webhook URL as parameter
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation
if [ $# -lt 3 ]; then
    echo -e "${RED}Error: Insufficient arguments${NC}"
    echo "Usage: $0 <webhook_url> <message> <color> [field_title field_value field_short...]"
    echo ""
    echo "Example:"
    echo "  $0 'https://hooks.slack.com/...' 'Deployment Started' '#36a64f' 'Env' 'Production' 'true'"
    exit 1
fi

WEBHOOK_URL="${1}"
MESSAGE="${2}"
COLOR="${3}"
shift 3 || true

# Validate webhook URL
if [[ ! "$WEBHOOK_URL" =~ ^https://hooks\.slack\.com/services/.+ ]]; then
    echo -e "${YELLOW}Warning: Webhook URL doesn't look like a Slack webhook${NC}"
fi

# Build fields array
FIELDS="[]"
while [[ $# -ge 3 ]]; do
    FIELD_TITLE="$1"
    FIELD_VALUE="$2"
    FIELD_SHORT="${3:-false}"
    shift 3 || break

    # Escape quotes in field values
    FIELD_TITLE_ESC=$(echo "$FIELD_TITLE" | jq -Rs .)
    FIELD_VALUE_ESC=$(echo "$FIELD_VALUE" | jq -Rs .)

    FIELDS=$(echo "$FIELDS" | jq \
        --arg title "$FIELD_TITLE" \
        --arg value "$FIELD_VALUE" \
        --argjson short "$FIELD_SHORT" \
        '. += [{"title": $title, "value": $value, "short": $short}]')
done

# Escape message for JSON
MESSAGE_ESC=$(echo "$MESSAGE" | jq -Rs .)

# Build and send payload
TIMESTAMP=$(date +%s)

PAYLOAD=$(jq -n \
    --arg message "$MESSAGE" \
    --arg color "$COLOR" \
    --argjson fields "$FIELDS" \
    --argjson ts "$TIMESTAMP" \
    '{
        "attachments": [{
            "color": $color,
            "text": $message,
            "fields": $fields,
            "footer": "HX-Citadel Automation",
            "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
            "ts": $ts
        }]
    }')

# Send notification
HTTP_CODE=$(curl -s -o /tmp/slack_response.txt -w "%{http_code}" \
    -X POST "$WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD")

# Check response
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Slack notification sent successfully${NC}"
    exit 0
else
    echo -e "${RED}❌ Slack notification failed (HTTP $HTTP_CODE)${NC}"
    cat /tmp/slack_response.txt
    exit 1
fi
