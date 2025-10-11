# Tech Knowledge Base Guide
## Your "Poor Man's MCP" - 67,000+ Reference Files

**Location**: `/home/agent0/workspace/hx-citadel-ansible/tech_kb/`
**Purpose**: Comprehensive reference library for all Shield technologies
**Total Repositories**: 33
**Total Files**: 67,000+

---

## 🎯 Quick Start

### The Big 5 (Most Valuable)

1. **`shield_mcp_complete/`** ⭐⭐⭐⭐⭐
   - **What**: Complete MCP server reference implementation
   - **Files**: 35
   - **Use**: Production-ready code examples for Phase 1
   - **Start here**: `README.md` - comprehensive implementation guide
   - **Example searches**:
     ```bash
     # Find MCP tool implementations
     ls tech_kb/shield_mcp_complete/implementation/mcp_server/src/

     # Study deployment scripts
     cat tech_kb/shield_mcp_complete/implementation/scripts/deployment/deploy_all.sh
     ```

2. **`ansible-devel/`** ⭐⭐⭐⭐⭐
   - **What**: Official Ansible 2.20 development repository
   - **Files**: 5,604
   - **Use**: FQCN syntax, module implementations
   - **Critical**: Never guess Ansible syntax - look it up here!
   - **Example searches**:
     ```bash
     # Find systemd module implementation
     cat tech_kb/ansible-devel/lib/ansible/modules/systemd.py

     # Find uri module for API calls
     cat tech_kb/ansible-devel/lib/ansible/modules/uri.py
     ```

3. **`fastmcp-main/`** ⭐⭐⭐⭐
   - **What**: FastMCP framework source code
   - **Files**: 629
   - **Use**: MCP tool patterns, server setup
   - **Example searches**:
     ```bash
     # Find tool decoration patterns
     grep -r "@mcp.tool" tech_kb/fastmcp-main/

     # Study server initialization
     cat tech_kb/fastmcp-main/src/fastmcp/server.py
     ```

4. **`LightRAG-main/`** ⭐⭐⭐⭐
   - **What**: LightRAG RAG engine source
   - **Files**: 401
   - **Use**: Knowledge graph, hybrid retrieval
   - **Example searches**:
     ```bash
     # Study LightRAG API
     cat tech_kb/LightRAG-main/lightrag/lightrag.py

     # Find KG construction
     grep -r "knowledge_graph" tech_kb/LightRAG-main/
     ```

5. **`litellm-main/`** ⭐⭐⭐⭐
   - **What**: LiteLLM gateway source
   - **Files**: 3,970
   - **Use**: Guardrails, routing, caching
   - **Example searches**:
     ```bash
     # Find guardrail examples
     grep -r "guardrail" tech_kb/litellm-main/

     # Study MCP gateway
     find tech_kb/litellm-main/ -name "*mcp*"
     ```

---

## 📚 Complete Directory Listing

### Core Frameworks (8)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| FastAPI | `fastapi/` | 2,551 | API development, async patterns, validation |
| FastMCP | `fastmcp-main/` | 629 | MCP tool creation, server setup |
| LightRAG | `LightRAG-main/` | 401 | RAG engine, knowledge graphs |
| LangGraph | `langgraph-main/` | 1,094 | Workflow orchestration, state graphs |
| LangGraph Examples | `langgraph-example-main/` | 40 | Practical LangGraph patterns |
| Pydantic | `pydantic-main/` | 483 | Data validation, type safety |
| LiteLLM | `litellm-main/` | 3,970 | LLM gateway, guardrails, routing |
| Ollama | `ollama-main/` | 963 | LLM deployment, model serving |

### UI & Frontend (7)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| CopilotKit | `CopilotKit-main/` | 2,821 | HITL UI, state streaming |
| AG-UI | `ag-ui-main/` | 696 | Event-driven UI, real-time updates |
| Open WebUI | `open-webui-main/` | 4,790 | Chat interface implementation |
| Next.js | `next.js-canary/` | 25,300 | React framework, SSR patterns |
| Zod | `zod-main/` | 536 | Schema validation |
| Zustand | `zustand-main/` | 137 | State management |
| Spec-Kit | `spec-kit-main/` | 56 | UI specifications |

### Data & Processing (7)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| Qdrant | `qdrant-master/` | 1,316 | Vector DB server implementation |
| Qdrant Client | `qdrant-client-master/` | 293 | Python client for vectors |
| Qdrant MCP Server | `mcp-server-qdrant-master/` | 30 | MCP integration for Qdrant |
| PostgreSQL | `postgres-master/` | 7,301 | Database internals, optimization |
| Prisma | `prisma-main/` | 4,448 | ORM, database migrations |
| Redis | `redis-unstable/` | 1,703 | Streams, caching, pub/sub |
| Crawl4AI | `crawl4ai-main/` | 628 | Web crawling, scraping |
| Docling | `docling-main/` | 710 | Document processing |

### Infrastructure (6)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| Ansible | `ansible-devel/` | 5,604 | Infrastructure automation |
| Docker CLI | `cli-master/` | 4,095 | Container management |
| Docker Compose | `compose-main/` | 645 | Multi-container orchestration |
| Docker Install | `docker-install-master/` | 13 | Docker setup scripts |
| Nginx | `nginx-master/` | 514 | Reverse proxy, load balancing |

### Design & Patterns (2)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| Agentic Patterns | `agentic-design-patterns-docs-main/` | 66 | Agent design patterns |
| Ottomator Agents | `ottomator-agents-main/` | 756 | Live agent studio examples |

### Reference Implementations (1)
| Technology | Directory | Files | Key Use Cases |
|-----------|-----------|-------|---------------|
| **Shield MCP Complete** ⭐ | `shield_mcp_complete/` | 35 | **Production-ready Shield implementation** |

---

## 🔍 How to Search Effectively

### 1. Find Implementation Examples
```bash
# Search for async functions across all repos
grep -r "async def" tech_kb/*/

# Find specific patterns (e.g., circuit breakers)
grep -r "circuit" tech_kb/fastmcp-main/

# Find configuration examples
find tech_kb/ -name "*.yaml" -o -name "*.yml" | head -20
```

### 2. Study Specific Technologies
```bash
# Ansible modules
ls tech_kb/ansible-devel/lib/ansible/modules/

# FastMCP examples
find tech_kb/fastmcp-main/examples/ -type f

# LightRAG API
cat tech_kb/LightRAG-main/README.md
```

### 3. Find Working Code
```bash
# Shield MCP implementation (MOST VALUABLE)
ls -la tech_kb/shield_mcp_complete/implementation/

# Database schemas
cat tech_kb/shield_mcp_complete/implementation/database/schemas/00_initial_schema.sql

# Deployment scripts
cat tech_kb/shield_mcp_complete/implementation/scripts/deployment/deploy_all.sh
```

---

## 💡 Use Cases by Scenario

### Scenario 1: Implementing a New MCP Tool
1. **Reference**: `tech_kb/shield_mcp_complete/implementation/mcp_server/src/main.py`
2. **Pattern**: `tech_kb/fastmcp-main/examples/`
3. **Validation**: `tech_kb/pydantic-main/docs/`

### Scenario 2: Writing Ansible Tasks
1. **Module syntax**: `tech_kb/ansible-devel/lib/ansible/modules/`
2. **Best practices**: `tech_kb/ansible-devel/docs/docsite/rst/`
3. **Examples**: Search for similar tasks in ansible-devel tests

### Scenario 3: Integrating LightRAG
1. **API reference**: `tech_kb/LightRAG-main/lightrag/`
2. **Usage examples**: `tech_kb/LightRAG-main/examples/`
3. **Shield integration**: `tech_kb/shield_mcp_complete/implementation/orchestrator/`

### Scenario 4: Configuring LiteLLM Gateway
1. **Configuration**: `tech_kb/litellm-main/litellm/proxy/`
2. **Guardrails**: `tech_kb/litellm-main/litellm/guardrails/`
3. **Shield config**: `tech_kb/shield_mcp_complete/implementation/litellm_gateway/`

### Scenario 5: Building UI with CopilotKit
1. **React hooks**: `tech_kb/CopilotKit-main/CopilotKit/packages/react-core/`
2. **UI components**: `tech_kb/CopilotKit-main/CopilotKit/packages/react-ui/`
3. **Examples**: `tech_kb/CopilotKit-main/examples/`

---

## 🎯 Quick Reference Commands

### Find READMEs (Entry Points)
```bash
find tech_kb/ -name "README.md" | sort
```

### Search for Specific Patterns
```bash
# Find all async implementations
grep -r "async def" tech_kb/fastmcp-main/ tech_kb/LightRAG-main/

# Find circuit breaker patterns
grep -r "CircuitBreaker" tech_kb/

# Find Redis Streams usage
grep -r "xadd\|xread" tech_kb/redis-unstable/
```

### Count Technologies
```bash
# Total directories
ls -1 tech_kb/ | wc -l

# Total files
find tech_kb/ -type f | wc -l

# Files by technology
for dir in tech_kb/*/; do
  echo "$(basename $dir): $(find $dir -type f | wc -l) files"
done
```

---

## ⚠️ Important Notes

### Do's
✅ **Use targeted searches** - Don't read entire repos
✅ **Start with shield_mcp_complete/** - Shield-specific implementations
✅ **Reference ansible-devel/** - Never guess Ansible syntax
✅ **Check README.md first** - Every repo has documentation
✅ **Search for patterns** - Use grep/find for specific examples

### Don'ts
❌ **Don't read everything** - 67,000 files is too much
❌ **Don't guess** - If you're unsure, search the knowledge base
❌ **Don't reinvent** - Check if it's already implemented
❌ **Don't copy blindly** - Understand the pattern first

---

## 📊 Statistics

- **Total Repositories**: 33
- **Total Files**: ~67,000
- **Total Lines of Code**: Millions
- **Languages**: Python, TypeScript, Go, Rust, Shell, YAML, SQL
- **Frameworks**: 15+
- **Databases**: 3 (PostgreSQL, Redis, Qdrant)
- **UI Frameworks**: 5+

---

## 🚀 Next Steps

1. ✅ **Explore shield_mcp_complete/** - Your primary reference
2. ✅ **Bookmark key directories** - Add to your mental map
3. ✅ **Practice searching** - Get familiar with grep/find
4. ✅ **Reference CLAUDE.md** - Updated with full tech_kb guide
5. ✅ **Use for Phase 2** - Type hints, testing, monitoring examples

---

## 🎉 Conclusion

This "poor man's MCP" is actually a **world-class knowledge base** containing:
- Complete source code for all Shield technologies
- Production-ready reference implementations
- Comprehensive examples and documentation
- Design patterns and best practices

**Value**: Immeasurable - this is the difference between guessing and knowing.

**Pro Tip**: When in doubt, search `tech_kb/shield_mcp_complete/` first - it's tailored specifically for Shield.

---

**Last Updated**: October 11, 2025
**Maintained by**: HX-Citadel Development Team
**Purpose**: Knowledge preservation and developer productivity
