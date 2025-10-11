# How to Create Linear Personal API Key

**Status**: You have the GitHub integration ✅, but we need a Personal API Key for scripts

---

## Step-by-Step Instructions

### 1. Go to Linear API Settings
Open this URL in your browser:
```
https://linear.app/settings/api
```

### 2. Look for "Personal API keys" Section
- You should see a section titled "Personal API keys"
- Below it says "Create API keys to use with the Linear API"

### 3. Click "Create new key"
- A dialog will appear

### 4. Fill in the Details
- **Label**: `HX-Citadel Automation`
- **Expiration**: Choose "Never" or "1 year"
- **Scopes**: This is CRITICAL!
  - You might see options like "Read", "Write", or checkboxes
  - **Select ALL scopes** or choose "Full access" if available
  - At minimum, you need:
    - ✅ Read issues
    - ✅ Read teams
    - ✅ Write issues (for updating)
    - ✅ Write comments

### 5. Create and COPY Immediately
- Click "Create key"
- **CRITICAL**: Copy the key IMMEDIATELY
- It starts with `lin_api_`
- Linear only shows it ONCE - you can't see it again!

### 6. Test the Key IMMEDIATELY

```bash
# Export the key
export LINEAR_API_KEY="lin_api_PASTE_YOUR_KEY_HERE"

# Test basic auth
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email } }"}'
```

**Expected result**:
```json
{
  "data": {
    "viewer": {
      "name": "Your Name",
      "email": "your@email.com"
    }
  }
}
```

**If you see "Authentication required"**:
- The key doesn't have the right scopes
- Delete it and create a new one with ALL scopes checked

### 7. Get Your Team Keys

```bash
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ teams { nodes { key name } } }"}'
```

This will show you team keys like "ENG", "PROD", "DEV" etc.

### 8. Test Full Integration

```bash
# Use a real issue ID from your Linear workspace
./scripts/test-linear-api.sh
```

This script will:
- ✅ Verify authentication
- ✅ List your teams
- ✅ Show example commands

---

## Troubleshooting

### "Authentication required, not authenticated"

**Cause**: Key doesn't have required scopes

**Fix**:
1. Go back to https://linear.app/settings/api
2. **Delete** the key you just created
3. Create a NEW key
4. This time, check **ALL scope boxes** or select "Full access"
5. Test immediately with the curl command above

### "Cannot find team"

**Cause**: Team key doesn't match your workspace

**Fix**:
1. Run the teams query (step 7 above)
2. Note the `key` values (e.g., "ENG", "PROD")
3. Use those exact keys in issue IDs

### Still Not Working?

**Check**:
1. Are you using the **Personal API Key** (not OAuth token)?
2. Did you copy the ENTIRE key including `lin_api_` prefix?
3. Did you check ALL scopes when creating the key?
4. Are you testing immediately (keys can't be retrieved later)?

---

## What's Different from GitHub Integration?

| Feature | GitHub OAuth Integration | Personal API Key |
|---------|-------------------------|------------------|
| **Purpose** | CodeRabbit auto-creates issues | Scripts fetch/update issues |
| **Where to get** | Linear Settings → Integrations | Linear Settings → API |
| **Format** | OAuth token (invisible) | `lin_api_xxxxx` |
| **Scopes** | Managed by OAuth flow | You choose when creating |
| **Used by** | CodeRabbit | Your automation scripts |

**You need BOTH!**
- ✅ GitHub integration (you have this) - for CodeRabbit
- ⏸️ Personal API Key (create this now) - for scripts

---

## Next Steps

1. ✅ Create Personal API Key with full scopes
2. ✅ Test with curl command
3. ✅ Run `./scripts/test-linear-api.sh`
4. ✅ Note your team keys
5. ✅ Test `./scripts/fetch-linear-issue.sh "TEAM-123"`

Once this works, the full automation will work!
