#!/usr/bin/env bash
# HX-Citadel FQDN Policy Enforcer
# Blocks commits with localhost, 127.0.0.1, ::1, or raw 192.168.10.x IPs

set -euo pipefail

START_TIME=$(date +%s)

# Paths to include/exclude
INCLUDE_ROOT="${1:-.}"

# Exclude common build/cache/vendor dirs; extend as needed
EXCLUDES=(
  ".git/**" ".github/**" ".venv/**" "venv/**" "node_modules/**" 
  "dist/**" "build/**" "coverage/**" "__pycache__/**" 
  "*.min.js" "*.lock" "*.pyc"
)

# Patterns to forbid (case-insensitive for localhost)
PATTERNS=(
  "\blocalhost\b"
  "\b127\.0\.0\.1\b"
  "\b::1\b"
  "\b192\.168\.10\.[0-9]{1,3}\b"
)

# Optional allowlist file
ALLOWLIST_FILE="${ALLOWLIST_FILE:-.fqdn-allowlist}"

# Detect tool: prefer ripgrep, fall back to grep
use_rg=0
if command -v rg >/dev/null 2>&1; then
  use_rg=1
fi

# Clean up temp file
rm -f /tmp/fqdn_hits.txt

if [[ $use_rg -eq 1 ]]; then
  # Build ripgrep args
  RG_ARGS=("--no-heading" "--hidden" "--follow" "--color=never")
  for g in "${EXCLUDES[@]}"; do 
    RG_ARGS+=("--glob" "!$g")
  done
  
  # Join patterns with |
  REGEX_PATTERN=$(IFS='|'; echo "${PATTERNS[*]}")
  
  rg "$REGEX_PATTERN" -nH "${RG_ARGS[@]}" "$INCLUDE_ROOT" > /tmp/fqdn_hits.txt 2>&1 || true
else
  # Fallback to grep -R with excludes
  GREP_ARGS=(
    "-R" "-nH" "--binary-files=without-match" 
    "--exclude-dir=.git" "--exclude-dir=.github" 
    "--exclude-dir=.venv" "--exclude-dir=venv" 
    "--exclude-dir=node_modules" "--exclude-dir=dist" 
    "--exclude-dir=build" "--exclude-dir=coverage" 
    "--exclude-dir=__pycache__"
    "--exclude=*.min.js" "--exclude=*.lock" "--exclude=*.pyc"
  )
  
  # Join patterns with |
  REGEX_PATTERN=$(IFS='|'; echo "${PATTERNS[*]}")
  
  grep "${GREP_ARGS[@]}" -Ei "$REGEX_PATTERN" "$INCLUDE_ROOT" > /tmp/fqdn_hits.txt 2>&1 || true
fi

# Apply allowlist if exists
if [[ -f "$ALLOWLIST_FILE" ]]; then
  while IFS= read -r pattern; do
    [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
    grep -v "$pattern" /tmp/fqdn_hits.txt > /tmp/fqdn_hits_filtered.txt 2>/dev/null || true
    mv /tmp/fqdn_hits_filtered.txt /tmp/fqdn_hits.txt 2>/dev/null || true
  done < "$ALLOWLIST_FILE"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Check results
if [[ -s /tmp/fqdn_hits.txt ]]; then
  echo "❌ Forbidden non-FQDN usage detected. Replace with FQDNs/short names (domain: dev-test.hana-x.ai)."
  echo "---"
  cat /tmp/fqdn_hits.txt
  echo "---"
  echo ""
  echo "Common replacements:"
  echo "  192.168.10.8  → hx-orchestrator-server.dev-test.hana-x.ai"
  echo "  192.168.10.9  → hx-vectordb-server.dev-test.hana-x.ai"
  echo "  192.168.10.48 → hx-sqldb-server.dev-test.hana-x.ai"
  echo "  192.168.10.50 → hx-ollama1.dev-test.hana-x.ai"
  echo "  localhost     → <service-hostname>.dev-test.hana-x.ai"
  echo ""
  echo "Full mapping: group_vars/all/fqdn_map.yml"
  echo "Tip: Use Ansible variables defined in group_vars/all; avoid hardcoding localhost and raw IPs."
  rm -f /tmp/fqdn_hits.txt
  exit 1
else
  echo "✅ FQDN policy check passed (scanned in ${DURATION}s)"
  rm -f /tmp/fqdn_hits.txt
  exit 0
fi
