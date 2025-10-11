# TASK-005: Test Document Processing
## Integration Test for ingest_doc() MCP Tool

**Date**: October 11, 2025  
**Tool**: `ingest_doc(file_path)`  
**Status**: ✅ READY FOR TESTING

---

## Test Objective

Verify that `ingest_doc()` successfully:
1. Processes PDF, DOCX, TXT, MD files using Docling
2. Extracts text content and metadata
3. Sends to orchestrator for async ingestion
4. Returns HTTP 202-style job_id
5. Handles unsupported formats gracefully

---

## Test Cases

### Test 1: PDF Document

**Setup**:
```bash
# Create test PDF (on hx-mcp1-server)
echo "Test PDF content" > /tmp/test.txt
# Convert to PDF or use existing PDF
```

**Input**:
```json
{
  "file_path": "/tmp/test.pdf"
}
```

**Expected Output**:
```json
{
  "status": "accepted",
  "message": "Document ingestion initiated for test.pdf",
  "job_id": "<uuid>",
  "source_name": "test.pdf",
  "file_format": ".pdf",
  "content_length": 1234,
  "page_count": 1,
  "check_status_endpoint": "/jobs/<uuid>"
}
```

---

### Test 2: Text File

**Setup**:
```bash
echo "This is a test document for ingestion." > /tmp/test.txt
```

**Input**:
```json
{
  "file_path": "/tmp/test.txt"
}
```

**Expected**:
- Processes successfully
- Returns job_id
- file_format=".txt"
- content_length > 0

---

### Test 3: Markdown File

**Setup**:
```bash
cat > /tmp/test.md << 'EOF'
# Test Document

## Section 1
This is a test markdown document.

### Subsection
- Bullet 1
- Bullet 2
EOF
```

**Input**:
```json
{
  "file_path": "/tmp/test.md"
}
```

**Expected**:
- Markdown processed
- Content extracted with formatting
- Metadata includes structure

---

### Test 4: File Not Found

**Input**:
```json
{
  "file_path": "/tmp/nonexistent-file.pdf"
}
```

**Expected Output**:
```json
{
  "status": "error",
  "error": "File not found: /tmp/nonexistent-file.pdf",
  "error_type": "file_not_found"
}
```

---

### Test 5: Unsupported Format

**Setup**:
```bash
echo "test" > /tmp/test.exe
```

**Input**:
```json
{
  "file_path": "/tmp/test.exe"
}
```

**Expected**:
- Error for unsupported format
- Helpful message listing supported formats

---

### Test 6: Circuit Breaker (Orchestrator Down)

**Setup**: Stop orchestrator

**Input**:
```json
{
  "file_path": "/tmp/test.txt"
}
```

**Expected**:
- Document processed successfully
- Circuit breaker prevents orchestrator call
- Returns error with retry_after

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| PDF processing | ✅ Works | ⏸️ Pending |
| DOCX processing | ✅ Works | ⏸️ Pending |
| TXT processing | ✅ Works | ⏸️ Pending |
| MD processing | ✅ Works | ⏸️ Pending |
| File not found | ✅ Error | ⏸️ Pending |
| Unsupported format | ✅ Error | ⏸️ Pending |
| Circuit breaker | ✅ Protected | ⏸️ Pending |
| HTTP 202 pattern | ✅ Followed | ⏸️ Pending |

---

**Implementation**: ✅ Complete (~200 LOC)  
**Testing**: ⏸️ Pending MCP client  
**Task Status**: Ready for integration testing

