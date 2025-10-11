#!/usr/bin/env bash
#
# Type Validation Script for HX-Citadel Shield
# Phase 2 Sprint 2.1: Type Hints Migration (TASK-029)
#
# This script validates type hints on deployed Python code.
# Since this is an Ansible project that generates Python from Jinja2 templates,
# type checking must be performed on the rendered Python files on target servers.
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_SERVER="hx-mcp1-server"
ORCHESTRATOR_SERVER="hx-orchestrator-server"
MCP_APP_DIR="/opt/hx-citadel-shield"
ORCHESTRATOR_APP_DIR="/opt/hx-citadel-shield/orchestrator"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      HX-Citadel Shield - Type Validation Script           ║${NC}"
echo -e "${BLUE}║      Phase 2 Sprint 2.1: Type Hints Migration             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to run mypy on a remote server
run_mypy_remote() {
    local server=$1
    local app_dir=$2
    local label=$3

    echo -e "${YELLOW}Validating type hints on ${label} (${server})...${NC}"

    # Check if mypy is installed
    if ! ssh "$server" "command -v mypy &> /dev/null"; then
        echo -e "${RED}✗ mypy not installed on ${server}${NC}"
        echo -e "  Install with: ssh ${server} 'pip install mypy'"
        return 1
    fi

    # Run mypy on the application directory
    if ssh "$server" "cd ${app_dir} && mypy . --config-file=/home/agent0/workspace/hx-citadel-ansible/mypy.ini 2>&1"; then
        echo -e "${GREEN}✓ Type validation passed for ${label}${NC}"
        return 0
    else
        echo -e "${RED}✗ Type validation failed for ${label}${NC}"
        return 1
    fi
}

# Function to run mypy locally on templates (with limitations)
run_mypy_local() {
    echo -e "${YELLOW}Validating type hints locally (limited - templates only)...${NC}"

    if ! command -v mypy &> /dev/null; then
        echo -e "${RED}✗ mypy not installed locally${NC}"
        echo -e "  Install with: pip install -r requirements-dev.txt"
        return 1
    fi

    # Note: This will have errors due to Jinja2 syntax, but can catch some issues
    echo -e "${BLUE}Note: Local validation has limitations due to Jinja2 templates${NC}"

    # Check if mypy.ini exists
    if [[ ! -f "mypy.ini" ]]; then
        echo -e "${RED}✗ mypy.ini not found${NC}"
        return 1
    fi

    # Run mypy on any Python files that exist
    if [[ -n "$(find . -name '*.py' -not -path './tech_kb/*' -not -path './.venv/*' 2>/dev/null)" ]]; then
        mypy . --config-file=mypy.ini || true
    else
        echo -e "${YELLOW}⚠ No Python files found to validate locally${NC}"
    fi

    echo -e "${GREEN}✓ Local validation complete${NC}"
    return 0
}

# Function to generate type coverage report
generate_coverage_report() {
    local server=$1
    local app_dir=$2
    local label=$3

    echo -e "${YELLOW}Generating type coverage report for ${label}...${NC}"

    if ssh "$server" "cd ${app_dir} && mypy . --config-file=/home/agent0/workspace/hx-citadel-ansible/mypy.ini --html-report /tmp/mypy-report 2>&1"; then
        echo -e "${GREEN}✓ Coverage report generated at ${server}:/tmp/mypy-report/index.html${NC}"

        # Try to extract coverage percentage
        if ssh "$server" "cd ${app_dir} && mypy . --config-file=/home/agent0/workspace/hx-citadel-ansible/mypy.ini 2>&1 | grep -oP 'Success.*'" || true; then
            :
        fi

        return 0
    else
        echo -e "${RED}✗ Coverage report generation failed${NC}"
        return 1
    fi
}

# Main validation logic
main() {
    local mode="${1:-remote}"
    local target="${2:-all}"

    case "$mode" in
        remote)
            case "$target" in
                mcp)
                    run_mypy_remote "$MCP_SERVER" "$MCP_APP_DIR" "MCP Server"
                    ;;
                orchestrator)
                    run_mypy_remote "$ORCHESTRATOR_SERVER" "$ORCHESTRATOR_APP_DIR" "Orchestrator"
                    ;;
                all)
                    echo -e "${BLUE}Validating both MCP Server and Orchestrator...${NC}"
                    echo ""

                    mcp_result=0
                    orch_result=0

                    run_mypy_remote "$MCP_SERVER" "$MCP_APP_DIR" "MCP Server" || mcp_result=$?
                    echo ""
                    run_mypy_remote "$ORCHESTRATOR_SERVER" "$ORCHESTRATOR_APP_DIR" "Orchestrator" || orch_result=$?

                    echo ""
                    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
                    if [[ $mcp_result -eq 0 && $orch_result -eq 0 ]]; then
                        echo -e "${GREEN}✓ All type validations passed!${NC}"
                        return 0
                    else
                        echo -e "${RED}✗ Some type validations failed${NC}"
                        return 1
                    fi
                    ;;
                *)
                    echo -e "${RED}✗ Invalid target: ${target}${NC}"
                    echo "  Valid targets: mcp, orchestrator, all"
                    return 1
                    ;;
            esac
            ;;
        local)
            run_mypy_local
            ;;
        report)
            case "$target" in
                mcp)
                    generate_coverage_report "$MCP_SERVER" "$MCP_APP_DIR" "MCP Server"
                    ;;
                orchestrator)
                    generate_coverage_report "$ORCHESTRATOR_SERVER" "$ORCHESTRATOR_APP_DIR" "Orchestrator"
                    ;;
                all)
                    generate_coverage_report "$MCP_SERVER" "$MCP_APP_DIR" "MCP Server"
                    generate_coverage_report "$ORCHESTRATOR_SERVER" "$ORCHESTRATOR_APP_DIR" "Orchestrator"
                    ;;
                *)
                    echo -e "${RED}✗ Invalid target for report: ${target}${NC}"
                    return 1
                    ;;
            esac
            ;;
        help|--help|-h)
            cat <<HELP_EOF
Usage: $0 [mode] [target]

Modes:
  remote    - Validate types on deployed servers (default)
  local     - Validate types locally (limited due to Jinja2 templates)
  report    - Generate HTML coverage reports
  help      - Show this help message

Targets:
  mcp           - MCP Server only
  orchestrator  - Orchestrator only
  all           - Both servers (default)

Examples:
  $0                          # Validate both servers remotely
  $0 remote mcp               # Validate MCP server only
  $0 local                    # Validate locally
  $0 report all               # Generate coverage reports

Requirements:
  - mypy installed on target servers: pip install mypy
  - SSH access to hx-mcp1-server and hx-orchestrator-server
  - Python code deployed via Ansible

HELP_EOF
            ;;
        *)
            echo -e "${RED}✗ Invalid mode: ${mode}${NC}"
            echo "  Run '$0 help' for usage information"
            return 1
            ;;
    esac
}

# Run main function
main "$@"
