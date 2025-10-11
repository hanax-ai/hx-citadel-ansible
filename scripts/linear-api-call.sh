#!/bin/bash
###############################################################################
# Linear API Call with Rate Limiting & Exponential Backoff
#
# Purpose: Safe wrapper for Linear API calls with automatic retry logic
# Usage: ./linear-api-call.sh <query_json_file>
#
# Features:
# - Exponential backoff (1s, 2s, 4s, 8s, 16s)
# - Rate limit detection (429 responses)
# - Circuit breaker (max 5 retries)
# - Structured logging
###############################################################################

set -euo pipefail

# Configuration
LINEAR_API_KEY="${LINEAR_API_KEY:-}"
QUERY_FILE="${1:-}"
MAX_RETRIES=5
INITIAL_DELAY=1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validation
if [[ -z "$LINEAR_API_KEY" ]]; then
    echo -e "${RED}Error: LINEAR_API_KEY not set${NC}" >&2
    exit 1
fi

if [[ -z "$QUERY_FILE" ]]; then
    echo -e "${RED}Error: Query file required${NC}" >&2
    echo "Usage: $0 <query_json_file>" >&2
    exit 1
fi

if [[ ! -f "$QUERY_FILE" ]]; then
    echo -e "${RED}Error: Query file not found: $QUERY_FILE${NC}" >&2
    exit 1
fi

###############################################################################
# Function: Make API Call with Retry Logic
###############################################################################
make_api_call() {
    local query_file="$1"
    local attempt=0
    local delay=$INITIAL_DELAY
    
    while [ $attempt -lt $MAX_RETRIES ]; do
        attempt=$((attempt + 1))
        
        echo -e "${BLUE}[Attempt $attempt/$MAX_RETRIES] Calling Linear API...${NC}" >&2
        
        # Make API call
        HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/linear_response.json \
            -X POST https://api.linear.app/graphql \
            -H "Authorization: $LINEAR_API_KEY" \
            -H "Content-Type: application/json" \
            -d "@$query_file")
        
        RESPONSE=$(cat /tmp/linear_response.json)
        
        # Success (200-299)
        if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
            echo -e "${GREEN}✅ API call successful (HTTP $HTTP_CODE)${NC}" >&2
            echo "$RESPONSE"
            return 0
        fi
        
        # Rate limited (429)
        if [[ "$HTTP_CODE" -eq 429 ]]; then
            # Check for Retry-After header (not available in curl -s -w)
            RETRY_AFTER=$(echo "$RESPONSE" | jq -r '.error.retryAfter // empty' 2>/dev/null || echo "")
            
            if [[ -n "$RETRY_AFTER" ]]; then
                delay=$RETRY_AFTER
            fi
            
            echo -e "${YELLOW}⚠️  Rate limited (HTTP 429). Retrying in ${delay}s...${NC}" >&2
            sleep "$delay"
            
            # Exponential backoff
            delay=$((delay * 2))
            if [[ $delay -gt 60 ]]; then
                delay=60  # Cap at 60 seconds
            fi
            
            continue
        fi
        
        # Client error (400-499, except 429)
        if [[ "$HTTP_CODE" -ge 400 && "$HTTP_CODE" -lt 500 ]]; then
            echo -e "${RED}❌ Client error (HTTP $HTTP_CODE)${NC}" >&2
            echo "$RESPONSE" >&2
            return 1
        fi
        
        # Server error (500-599)
        if [[ "$HTTP_CODE" -ge 500 ]]; then
            echo -e "${YELLOW}⚠️  Server error (HTTP $HTTP_CODE). Retrying in ${delay}s...${NC}" >&2
            sleep "$delay"
            
            # Exponential backoff
            delay=$((delay * 2))
            if [[ $delay -gt 60 ]]; then
                delay=60
            fi
            
            continue
        fi
        
        # Unexpected status code
        echo -e "${RED}❌ Unexpected HTTP code: $HTTP_CODE${NC}" >&2
        echo "$RESPONSE" >&2
        return 1
    done
    
    # Max retries exceeded
    echo -e "${RED}❌ Max retries ($MAX_RETRIES) exceeded${NC}" >&2
    return 1
}

###############################################################################
# Main
###############################################################################

# Execute API call with retry logic
make_api_call "$QUERY_FILE"

# Cleanup
rm -f /tmp/linear_response.json

