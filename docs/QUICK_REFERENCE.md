# Quick Reference Guide
## Production Parity Enhancement - Fast Lookup

**Version**: 1.0  
**Date**: October 10, 2025  
**Related**: CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md

---

## 📋 DOCUMENT INDEX

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md** | Strategic plan with detailed gap analysis | Understanding what needs to be done and why |
| **IMPLEMENTATION_CHECKLIST.md** | Task-by-task execution tracker | During implementation to track progress |
| **ASYNC_JOB_PATTERN.md** | HTTP 202 pattern implementation guide | Implementing async operations |
| **CIRCUIT_BREAKER_GUIDE.md** | Circuit breaker pattern guide | Adding resilience to service calls |
| **TYPE_HINTS_MIGRATION_GUIDE.md** | Type hints implementation guide | Adding type annotations |
| **QUICK_REFERENCE.md** (this doc) | Fast command and code lookup | Quick reference during coding |

---

## 🚀 QUICK START

### Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check Ansible version
ansible --version

# Check connectivity to servers
ansible all -i inventory/prod.ini -m ping

# Check git status
git status
git branch
```

### Create Feature Branch

```bash
# Create and checkout feature branch
git checkout -b feature/production-parity

# Or for specific sprints
git checkout -b feature/mcp-tool-implementations
git checkout -b feature/circuit-breakers
git checkout -b feature/async-pattern
```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install additional dev tools
pip install mypy pytest pytest-asyncio locust
```

---

## 📦 DEPENDENCY ADDITIONS

### Phase 1 Dependencies

```txt
# Add to roles/fastmcp_server/files/requirements.txt

# Crawl4AI and Docling
crawl4ai>=0.3.0
docling>=1.0.0
python-multipart>=0.0.6

# Circuit Breaker
circuitbreaker==1.4.0

# Prometheus
prometheus-client>=0.19.0

# Type checking (dev)
mypy==1.7.0
types-redis==4.6.0
types-requests==2.31.0
```

### Install Command

```bash
# Install on control node
pip install -r roles/fastmcp_server/files/requirements.txt

# Or deploy via Ansible
ansible-playbook -i inventory/prod.ini site.yml --tags fastmcp
```

---

## 🔧 COMMON CODE PATTERNS

### Circuit Breaker Wrapper

```python
from circuitbreaker import circuit
import httpx

@circuit(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=httpx.HTTPError
)
async def call_orchestrator_api(
    endpoint: str,
    data: dict
) -> dict:
    """Call orchestrator with circuit breaker protection."""
    url = f"{ORCHESTRATOR_URL}{endpoint}"
    response = await http_client.post(url, json=data, timeout=30.0)
    response.raise_for_status()
    return response.json()
```

### HTTP 202 Response Pattern

```python
@mcp.tool()
async def crawl_web(url: str) -> dict:
    """Crawl website asynchronously."""
    try:
        result = await call_orchestrator_api("/ingest-async", {
            "source_type": "web_crawl",
            "source_uri": url
        })
        
        return {
            "status": "queued",
            "job_id": result["job_id"],
            "message": f"Crawling {url} queued",
            "track_url": f"/jobs/{result['job_id']}",
            "estimated_time": "2-5 minutes"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
tool_calls_total = Counter(
    'shield_mcp_tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

tool_duration = Histogram(
    'shield_mcp_tool_duration_seconds',
    'Tool execution duration',
    ['tool_name']
)

# Instrument function
@mcp.tool()
async def my_tool():
    start_time = time.time()
    tool_calls_total.labels(tool_name='my_tool', status='started').inc()
    
    try:
        result = await do_work()
        tool_calls_total.labels(tool_name='my_tool', status='success').inc()
        return result
    except Exception as e:
        tool_calls_total.labels(tool_name='my_tool', status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        tool_duration.labels(tool_name='my_tool').observe(duration)

# Start metrics server
start_http_server(9090)
```

### Type Hints Template

```python
from typing import Dict, Any, List, Optional

async def function_name(
    param1: str,
    param2: int = 10,
    param3: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Function description.
    
    Args:
        param1: Description
        param2: Description with default
        param3: Optional description
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
    result: Dict[str, Any] = {"key": "value"}
    return result
```

---

## 🧪 TESTING COMMANDS

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_circuit_breaker.py

# Run with coverage
pytest tests/unit/ --cov=roles --cov-report=html

# Run with verbose output
pytest tests/unit/ -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/

# Run specific test
pytest tests/integration/test_mcp_tools.py

# Skip slow tests
pytest tests/integration/ -m "not slow"
```

### Type Checking

```bash
# Check all files
mypy roles/ --config-file=mypy.ini

# Check specific file
mypy roles/fastmcp_server/templates/shield_mcp_server.py.j2

# Generate HTML report
mypy roles/ --html-report mypy-report/

# Strict mode
mypy roles/ --strict
```

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/load/mcp_tools.py --host http://localhost:8000

# Headless mode (no web UI)
locust -f tests/load/mcp_tools.py --host http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless
```

---

## 🔍 DEBUGGING COMMANDS

### Check Service Status

```bash
# MCP server
systemctl status shield-mcp-server
journalctl -u shield-mcp-server -f

# Orchestrator
systemctl status shield-orchestrator
journalctl -u shield-orchestrator -f

# Check if services are listening
netstat -tlnp | grep 8000  # MCP server
netstat -tlnp | grep 8001  # Orchestrator
```

### Check Metrics

```bash
# MCP server metrics
curl http://localhost:9090/metrics | grep shield_mcp

# Orchestrator metrics
curl http://localhost:9091/metrics | grep shield_orchestrator

# Circuit breaker state
curl http://localhost:9090/metrics | grep circuit_breaker_state
```

### Check Redis

```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Check job status
redis-cli GET "job:abc123"
redis-cli HGETALL "job:abc123"

# Check stream
redis-cli XLEN ingest_jobs
redis-cli XREAD STREAMS ingest_jobs 0

# Check circuit breaker failures
redis-cli GET "circuit_breaker:orchestrator:failures"
```

### Check Qdrant

```bash
# Check collections
curl http://localhost:6333/collections

# Check collection info
curl http://localhost:6333/collections/knowledge_base

# Search test
curl -X POST http://localhost:6333/collections/knowledge_base/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 5
  }'
```

### Check Prometheus

```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq

# Query metric
curl 'http://localhost:9090/api/v1/query?query=shield_mcp_tool_calls_total'

# Check alerts
curl http://localhost:9090/api/v1/alerts | jq
```

---

## 📊 ANSIBLE COMMANDS

### Deploy Changes

```bash
# Full deployment
ansible-playbook -i inventory/prod.ini site.yml

# Deploy only MCP server
ansible-playbook -i inventory/prod.ini site.yml --tags fastmcp

# Deploy only orchestrator
ansible-playbook -i inventory/prod.ini site.yml --tags orchestrator

# Dry run
ansible-playbook -i inventory/prod.ini site.yml --check

# Verbose output
ansible-playbook -i inventory/prod.ini site.yml -vvv
```

### Restart Services

```bash
# Restart MCP server on all nodes
ansible -i inventory/prod.ini mcp_nodes -m systemd \
  -a "name=shield-mcp-server state=restarted" --become

# Restart orchestrator
ansible -i inventory/prod.ini orchestrator_nodes -m systemd \
  -a "name=shield-orchestrator state=restarted" --become

# Check service status
ansible -i inventory/prod.ini all -m systemd \
  -a "name=shield-mcp-server" --become
```

### Update Configuration

```bash
# Deploy only configuration files
ansible-playbook -i inventory/prod.ini playbooks/deploy-base.yml --tags config

# Update environment variables
ansible -i inventory/prod.ini all -m template \
  -a "src=templates/app.env.j2 dest=/opt/shield/.env" --become

# Reload systemd after config change
ansible -i inventory/prod.ini all -m systemd \
  -a "daemon_reload=yes" --become
```

---

## 🔐 GIT WORKFLOW

### Commit Changes

```bash
# Stage changes
git add roles/fastmcp_server/templates/shield_mcp_server.py.j2

# Commit with descriptive message
git commit -m "feat: implement crawl_web tool with Crawl4AI integration

- Add Crawl4AI library integration
- Implement async web crawling
- Add error handling for 403/404
- Return HTTP 202 with job_id
- Add Prometheus metrics

Refs: #123"

# Push to remote
git push origin feature/mcp-tool-implementations
```

### Create Pull Request

```bash
# Push branch
git push -u origin feature/production-parity

# Create PR via GitHub CLI (if installed)
gh pr create --title "Production Parity Enhancements" \
             --body "Implements all enhancements from CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md"

# Or create via web interface
# https://github.com/hanax-ai/hx-citadel-ansible/compare/main...feature/production-parity
```

### Tag Release

```bash
# After Phase 1 completion
git tag -a v1.1.0-phase1 -m "Phase 1: Critical fixes complete"
git push origin v1.1.0-phase1

# After all phases
git tag -a v1.1.0 -m "Production parity complete"
git push origin v1.1.0
```

---

## 📈 MONITORING QUERIES

### Prometheus Queries

```promql
# Tool call rate
rate(shield_mcp_tool_calls_total[5m])

# Tool error rate
rate(shield_mcp_tool_calls_total{status="error"}[5m])

# Tool p95 latency
histogram_quantile(0.95, rate(shield_mcp_tool_duration_seconds_bucket[5m]))

# Circuit breaker state
shield_mcp_circuit_breaker_state

# Active jobs
shield_active_jobs

# Queue depth
shield_worker_queue_size
```

### Alert Conditions

```yaml
# High error rate
rate(shield_mcp_tool_calls_total{status="error"}[5m]) > 0.1

# Circuit breaker open
shield_mcp_circuit_breaker_state == 1

# High latency
histogram_quantile(0.95, rate(shield_mcp_tool_duration_seconds_bucket[5m])) > 5

# Queue backup
shield_worker_queue_size > 100

# No requests (service down)
rate(shield_mcp_tool_calls_total[5m]) == 0
```

---

## 🐛 TROUBLESHOOTING SHORTCUTS

### MCP Server Not Starting

```bash
# Check logs
journalctl -u shield-mcp-server -n 100 --no-pager

# Check config
cat /opt/shield/mcp/.env

# Check port
netstat -tlnp | grep 8000

# Test manually
python /opt/shield/mcp/shield_mcp_server.py
```

### Circuit Breaker Stuck Open

```bash
# Check circuit state
curl http://localhost:9090/metrics | grep circuit_breaker_state

# Check orchestrator health
curl http://orchestrator:8001/health

# Manually reset (if needed - use with caution)
# This requires code access to circuit breaker instance
python -c "from shield_mcp_server import call_orchestrator_api; call_orchestrator_api._circuit_breaker.call_succeeded()"
```

### Job Stuck in Queue

```bash
# Check Redis stream
redis-cli XLEN ingest_jobs

# Check worker status
curl http://orchestrator:8001/health/workers

# Check job details
redis-cli HGETALL "job:abc123-def456-789"

# Restart workers
systemctl restart shield-orchestrator-workers
```

### Metrics Not Showing

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="mcp-server")'

# Check Prometheus logs
journalctl -u prometheus -f

# Reload Prometheus config
systemctl reload prometheus
```

---

## 📚 USEFUL LINKS

### Internal Documentation

- [Main Recommendations](./CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md)
- [Implementation Checklist](./IMPLEMENTATION_CHECKLIST.md)
- [Async Job Pattern Guide](./guides/ASYNC_JOB_PATTERN.md)
- [Circuit Breaker Guide](./guides/CIRCUIT_BREAKER_GUIDE.md)
- [Type Hints Guide](./guides/TYPE_HINTS_MIGRATION_GUIDE.md)

### External Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Circuit Breaker Library](https://pypi.org/project/circuitbreaker/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Crawl4AI Documentation](https://github.com/unclecode/crawl4ai)

### Reference Implementations

- `tech_kb/shield_mcp_complete/implementation/` - Full reference
- `tech_kb/.../mcp_server/src/main.py` - MCP server example
- `tech_kb/.../orchestrator/src/main.py` - Orchestrator example

---

## 💡 TIPS & TRICKS

### Speed Up Development

```bash
# Use pytest markers for quick tests
pytest -m "not slow" tests/

# Use mypy cache
mypy roles/ --cache-dir .mypy_cache/

# Use pytest-xdist for parallel testing
pip install pytest-xdist
pytest -n auto tests/

# Use watchdog for auto-reload during development
pip install watchdog
watchmedo auto-restart --patterns="*.py" python shield_mcp_server.py
```

### Code Quality Shortcuts

```bash
# Format code with black
black roles/ --line-length 100

# Sort imports with isort
isort roles/

# Lint with flake8
flake8 roles/ --max-line-length 100

# All in one (if pre-commit configured)
pre-commit run --all-files
```

### Performance Testing

```bash
# Quick load test with ab
ab -n 1000 -c 10 http://localhost:8000/mcp/crawl_web

# Profile Python code
python -m cProfile -o profile.stats shield_mcp_server.py
python -m pstats profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler shield_mcp_server.py
```

---

## 📞 SUPPORT

### Team Contacts

- **Tech Lead**: [Name] - [Email/Slack]
- **DevOps**: [Name] - [Email/Slack]
- **On-Call**: Check PagerDuty rotation

### Escalation Path

1. **Level 1**: Check this guide and documentation
2. **Level 2**: Team Slack channel (#shield-dev)
3. **Level 3**: Tech lead
4. **Level 4**: Engineering manager

### Emergency Procedures

```bash
# Emergency rollback
ansible-playbook -i inventory/prod.ini rollback.yml --extra-vars "version=v1.0.0"

# Emergency stop (if causing issues)
ansible -i inventory/prod.ini all -m systemd \
  -a "name=shield-mcp-server state=stopped" --become

# Emergency circuit breaker (force close)
# Contact DevOps - requires direct Redis access
```

---

**Document Status**: ✅ **ACTIVE**  
**Last Updated**: October 10, 2025  
**Next Review**: Monthly or as needed

