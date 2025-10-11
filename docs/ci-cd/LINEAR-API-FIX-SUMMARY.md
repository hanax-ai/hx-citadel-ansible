# Linear API Integration - Fix Summary

**Date**: October 11, 2025
**Status**: ✅ **COMPLETE**
**Issues Fixed**: 2 critical Linear API integration bugs

---

## Problems Identified

CodeRabbit identified 2 critical issues preventing the Linear integration from working:

### Issue #1: Missing "Bearer" Prefix in Authorization Header
**Severity**: 🔴 Critical
**Impact**: All Linear API requests were failing with 401 Unauthorized

**Problem**: Linear's GraphQL API requires the Authorization header to be formatted as:
```
Authorization: Bearer <api-key>
```

But our code was sending:
```
Authorization: <api-key>
```

**Result**: Every API request returned 401 and the automation workflow exited before reading any issue data.

### Issue #2: Incorrect GraphQL Query for Human-Friendly Identifiers
**Severity**: 🔴 Critical
**Impact**: Could not fetch Linear issues using identifiers like "DEV-123"

**Problem**: The workflow was using `issue(id:)` query which expects opaque global IDs (e.g., `f45d...`), but we were passing human-friendly identifiers like "DEV-123".

**Result**: Query always failed with `{"data":{"issue":null}}` because Linear couldn't find issues with those IDs.

---

## Solutions Implemented

### Solution #1: Added "Bearer" Prefix to All Linear API Calls ✅

**Files Modified**:
1. `.github/workflows/ai-fix-coderabbit-issues.yml` (line 305)
2. `scripts/fetch-linear-issue.sh` (lines 35, 51)

**Changes**:
```bash
# Before (BROKEN):
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  ...

# After (FIXED):
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: Bearer $LINEAR_API_KEY" \
  ...
```

**Testing**: Script syntax validated ✅

### Solution #2: Created Smart Linear Issue Fetcher ✅

**New File**: `scripts/fetch-linear-issue.sh`

This helper script intelligently handles both identifier formats:

#### For Human-Friendly IDs (e.g., "DEV-123"):
1. Parse identifier into team key ("DEV") and issue number (123)
2. Query Linear for team ID using team key filter
3. Fetch issue using team + number filters
4. Return issue details as JSON

#### For Global IDs (backward compatibility):
1. Use the standard `issue(id:)` query directly
2. Return issue details as JSON

**Benefits**:
- ✅ Works with both "DEV-123" and global IDs
- ✅ Single reusable script for all Linear API fetches
- ✅ Proper error handling and validation
- ✅ Returns clean JSON output

**Integration Points**:
1. `.github/workflows/ai-fix-coderabbit-issues.yml` - Uses script to fetch issues (line 76)
2. `scripts/fix-linear-issue.sh` - Refactored to use helper script (line 58)

---

## Testing Performed

### ✅ Bash Syntax Validation
```bash
bash -n scripts/fetch-linear-issue.sh
✅ Script syntax is valid

bash -n scripts/fix-linear-issue.sh
✅ Script syntax is valid
```

### ⏸️ Live API Testing
- **Status**: Pending LINEAR_API_KEY environment variable
- **Next Step**: Set LINEAR_API_KEY secret in GitHub repository
- **Test Command**:
  ```bash
  export LINEAR_API_KEY="lin_api_..."
  ./scripts/fetch-linear-issue.sh "DEV-123"
  ```

---

## Files Changed

### Modified Files
1. `.github/workflows/ai-fix-coderabbit-issues.yml`
   - Replaced inline GraphQL with helper script call (lines 70-105)
   - Added "Bearer" prefix to mutation call (line 305)
   - Added error handling and validation

2. `scripts/fix-linear-issue.sh`
   - Refactored `fetch_linear_issue()` function (lines 48-68)
   - Now uses `fetch-linear-issue.sh` helper
   - Maintains backward compatibility with existing code

### New Files
3. `scripts/fetch-linear-issue.sh` (**NEW**)
   - 68 lines of bash
   - Handles human-friendly IDs (DEV-123) and global IDs
   - Proper error handling and JSON output
   - Executable: `chmod +x`

---

## Impact Assessment

### Before Fixes ❌
- Linear API calls: **100% failure rate** (401 Unauthorized)
- Issue fetching: **0% success** (wrong query type)
- Automation workflow: **Completely broken**

### After Fixes ✅
- Linear API authentication: **Expected to work** (Bearer prefix added)
- Issue fetching: **Expected to work** (smart query logic)
- Automation workflow: **Ready for testing**

---

## Next Steps

### Immediate (Required for Testing)
1. ✅ **DONE**: Fix code and commit changes
2. ⏸️ **PENDING**: Set `LINEAR_API_KEY` secret in GitHub repository
3. ⏸️ **PENDING**: Test with manual workflow dispatch:
   ```bash
   gh workflow run ai-fix-coderabbit-issues.yml \
     -f issue_id="DEV-123" \
     -f severity="high"
   ```

### Validation Steps
1. Check GitHub Actions logs for successful Linear API fetch
2. Verify issue details are correctly extracted
3. Confirm PR is created and linked back to Linear
4. Test with both human-friendly IDs and global IDs

### Documentation Updates
1. Update `CODERABBIT-FIX-STATUS.md` with completion status
2. Add testing results to `PHASE-2A-DEPLOYMENT-CHECKLIST.md`
3. Document Linear API troubleshooting in `CODERABBIT-AUTOMATION.md`

---

## References

- **CodeRabbit Review**: `docs/ci-cd/coderabbit-linear-automation.md`
- **Original Issue Tracker**: `docs/ci-cd/CODERABBIT-FIX-STATUS.md`
- **Linear API Docs**: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- **GitHub Workflow**: `.github/workflows/ai-fix-coderabbit-issues.yml`

---

## Lessons Learned

1. **Always use "Bearer" prefix** for Linear API authentication
2. **Human-friendly IDs require different queries** than global IDs
3. **Extract complex logic to helper scripts** instead of inline YAML
4. **Test API integration early** before building automation on top

---

**Status**: ✅ Code fixes complete, awaiting LINEAR_API_KEY for live testing
**Confidence**: **HIGH** - Both issues identified by CodeRabbit have been addressed
**Risk**: **LOW** - Changes are isolated to Linear API integration layer
