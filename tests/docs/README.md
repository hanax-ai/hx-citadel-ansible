# Test Procedures

Manual test procedures and test case documentation.

## Test Procedures

### MCP Server Tests
- **TEST-004-web-crawling.md** - Web crawling functionality tests
  - Tests `crawl_web` MCP tool
  - Validates URL parsing, content extraction
  - Expected outputs and error cases

- **TEST-005-document-processing.md** - Document ingestion tests
  - Tests `ingest_doc` MCP tool
  - Validates multi-format support (PDF, TXT, Markdown)
  - Chunking and embedding generation

### Vector Database Tests
- **TEST-009-qdrant-operations.md** - Qdrant vector operations tests
  - Tests `qdrant_find` and `qdrant_store` tools
  - Validates vector search and storage
  - Metadata filtering and similarity scoring

### End-to-End Tests
- **TEST-011-lightrag-e2e.md** - LightRAG end-to-end workflow tests
  - Tests `lightrag_query` tool
  - Validates knowledge graph construction
  - Hybrid retrieval (KG + Vector) testing

## Usage

These are manual test procedures. To execute:

1. Read the test procedure document
2. Follow steps sequentially
3. Verify expected outputs
4. Document any failures

## Test Coverage

| Component | Test ID | Status |
|-----------|---------|--------|
| Web Crawling | TEST-004 | ✅ Documented |
| Document Processing | TEST-005 | ✅ Documented |
| Qdrant Operations | TEST-009 | ✅ Documented |
| LightRAG E2E | TEST-011 | ✅ Documented |

## Automation

These manual tests should eventually be automated as integration tests in `tests/integration/`.
