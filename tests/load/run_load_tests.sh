#!/usr/bin/env bash
#
#
#
#
#
#

set -euo pipefail

MCP_SERVER_URL="${MCP_SERVER_URL:-http://hx-mcp1-server:8081}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://hx-orchestrator-server:8000}"
QDRANT_URL="${QDRANT_URL:-http://hx-vectordb-server:6333}"
RESULTS_DIR="tests/load/results"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$RESULTS_DIR"

show_help() {
    echo "HX-Citadel Shield Load Test Runner"
    echo ""
    echo "Usage:"
    echo "  ./run_load_tests.sh [scenario] [options]"
    echo ""
    echo "Scenarios:"
    echo "  normal      - Normal load (100 users, 60s)"
    echo "  stress      - Stress test (500 users, 300s)"
    echo "  spike       - Spike test (0→1000 users)"
    echo "  endurance   - Endurance test (100 users, 3600s)"
    echo "  circuit     - Circuit breaker test (50 users, 180s)"
    echo "  orchestrator - Orchestrator API (50 users, 60s)"
    echo "  qdrant      - Qdrant operations (100 users, 60s)"
    echo "  all         - Run all scenarios sequentially"
    echo ""
    echo "Options:"
    echo "  --host URL  - Override MCP server URL"
    echo "  --help      - Show this help message"
    echo ""
    exit 0
}

run_scenario() {
    local scenario=$1
    local locustfile=$2
    local users=$3
    local spawn_rate=$4
    local run_time=$5
    local host=${6:-$MCP_SERVER_URL}
    
    echo -e "${GREEN}Running $scenario scenario...${NC}"
    echo "  Users: $users"
    echo "  Spawn rate: $spawn_rate/s"
    echo "  Duration: $run_time"
    echo "  Host: $host"
    echo ""
    
    locust \
        -f "tests/load/locustfiles/$locustfile" \
        --host="$host" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="$run_time" \
        --headless \
        --html="$RESULTS_DIR/${scenario}_report.html" \
        --csv="$RESULTS_DIR/${scenario}" \
        --logfile="$RESULTS_DIR/${scenario}.log" \
        || true
    
    echo -e "${GREEN}✓ $scenario complete${NC}"
    echo "  Report: $RESULTS_DIR/${scenario}_report.html"
    echo ""
}

main() {
    local scenario="${1:-normal}"
    
    if [[ "$scenario" == "--help" ]] || [[ "$scenario" == "-h" ]]; then
        show_help
    fi
    
    if ! command -v locust &> /dev/null; then
        echo -e "${RED}Error: locust is not installed${NC}"
        echo "Install with: pip install -r requirements-dev.txt"
        exit 1
    fi
    
    echo -e "${YELLOW}HX-Citadel Shield Load Testing${NC}"
    echo "================================"
    echo ""
    
    case "$scenario" in
        normal)
            run_scenario "normal_load" "mcp_server.py" 100 10 "60s" "$MCP_SERVER_URL"
            ;;
        stress)
            run_scenario "stress_test" "mcp_server.py" 500 50 "300s" "$MCP_SERVER_URL"
            ;;
        spike)
            echo -e "${YELLOW}Spike test: 0 → 1000 users${NC}"
            run_scenario "spike_test" "mcp_server.py" 1000 100 "120s" "$MCP_SERVER_URL"
            ;;
        endurance)
            run_scenario "endurance_test" "mcp_server.py" 100 10 "3600s" "$MCP_SERVER_URL"
            ;;
        circuit)
            run_scenario "circuit_breaker" "circuit_breaker.py" 50 10 "180s" "$MCP_SERVER_URL"
            ;;
        orchestrator)
            run_scenario "orchestrator_load" "orchestrator_api.py" 50 5 "60s" "$ORCHESTRATOR_URL"
            ;;
        qdrant)
            run_scenario "qdrant_load" "qdrant_operations.py" 100 10 "60s" "$QDRANT_URL"
            ;;
        all)
            echo -e "${YELLOW}Running all load test scenarios...${NC}"
            echo ""
            run_scenario "normal_load" "mcp_server.py" 100 10 "60s" "$MCP_SERVER_URL"
            run_scenario "stress_test" "mcp_server.py" 500 50 "300s" "$MCP_SERVER_URL"
            run_scenario "spike_test" "mcp_server.py" 1000 100 "120s" "$MCP_SERVER_URL"
            run_scenario "circuit_breaker" "circuit_breaker.py" 50 10 "180s" "$MCP_SERVER_URL"
            run_scenario "orchestrator_load" "orchestrator_api.py" 50 5 "60s" "$ORCHESTRATOR_URL"
            run_scenario "qdrant_load" "qdrant_operations.py" 100 10 "60s" "$QDRANT_URL"
            echo -e "${GREEN}All scenarios complete!${NC}"
            ;;
        *)
            echo -e "${RED}Error: Unknown scenario '$scenario'${NC}"
            echo ""
            show_help
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}Load testing complete!${NC}"
    echo "Results: $RESULTS_DIR/"
}

main "$@"
