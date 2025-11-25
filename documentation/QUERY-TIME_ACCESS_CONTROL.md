# Azure AI Search Query-Time Security Trimming

## Overview

This implementation uses **query-time access control** with Azure AI Search, where the search service automatically filters results based on the user's token permissions. This eliminates the need for manual OData filter construction in the application code.

> **Configuration:** All settings are centralized in `config.py` (Python) and `config.js` (React). See [CONFIGURATION.md](../msal-react-obo-sample/CONFIGURATION.md) for setup details.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User authenticates with Entra ID                             │
│    React SPA → Entra ID → Returns access token                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. React app acquires token for Python API                      │
│    Scope: api://<YOUR_API_CLIENT_ID>/access_as_user             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Python API performs OBO token exchange                       │
│    User token → MSAL OBO → Azure Search token                   │
│    Scope: https://search.azure.com/.default                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Python API calls Azure AI Search with headers                │
│    Authorization: Bearer <search_token>                         │
│    x-ms-query-source-authorization: <search_token>              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Azure AI Search evaluates token and filters results          │
│    - Extracts user's OID from token                             │
│    - Extracts user's group memberships from token               │
│    - Returns only documents where:                              │
│      • UserIds collection contains user's OID, OR               │
│      • GroupIds collection contains user's group IDs            │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Python API Code (app.py)

**OBO Token Exchange (Lines 440-452)**
```python
result = msal_app.acquire_token_on_behalf_of(
    user_assertion=user_access_token,
    scopes=SEARCH_SCOPE  # ["https://search.azure.com/.default"]
)

if "error" in result:
    # Handle OBO error
    return jsonify({"error": "OBO token acquisition failed"}), 500

search_access_token = result['access_token']
```

**Headers Configuration (Lines 457-460)**
```python
headers = {
    "Authorization": f"Bearer {search_access_token}",
    "x-ms-query-source-authorization": search_access_token,
    "Content-Type": "application/json"
}
```

**API Request (Lines 478-486)**
```python
search_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version=2025-11-01-preview"

payload = {
    "search": search_query,
    "select": "name,description,location,GroupIds,UserIds",
    "top": 50,
    "queryType": "simple",
    "orderby": "name asc"
}
# No manual filter needed - Azure AI Search handles access control
```

### Key Configuration

**Index:** `<YOUR_INDEX_NAME>` (configured in `config.py`)

**Search Endpoint:** `https://<YOUR_SEARCH_SERVICE>.search.windows.net` (configured in `config.py`)

**API Version:** `2025-11-01-preview` (required for query-time access control)

**Authentication Mode:** `SEARCH_AUTH_MODE=OBO` (default, can be set via environment variable)

## Index Schema Requirements

For query-time access control to work, the index must have these fields:

### Required ACL Fields

1. **`UserIds`** (Collection of Edm.String)
   - Contains Object IDs (OIDs) of users authorized to access the document
   - Example: `["590cc83d-d461-4a20-9cc1-f3f631e88366"]`

2. **`GroupIds`** (Collection of Edm.String)
   - Contains Entra ID group IDs that have access to the document
   - Example: `["group-id-1", "group-id-2"]`

### Content Fields

3. **`name`** (Edm.String) - Document name/title
4. **`description`** (Edm.String) - Document description
5. **`location`** (Edm.String) - Geographic location or other metadata

## How Query-Time Access Control Works

### Token Evaluation

When Azure AI Search receives a request with the `x-ms-query-source-authorization` header:

1. **Token Validation**
   - Validates the JWT signature
   - Checks token expiration
   - Verifies the audience matches the search service

2. **Claims Extraction**
   - Extracts `oid` (Object ID) claim - user's unique identifier
   - Extracts `groups` claim - user's group memberships (if present)

3. **Automatic Filtering**
   - Applies security filter automatically
   - No OData filter construction needed in application code
   - Filter logic: `(UserIds/any(u: u eq '<user_oid>')) OR (GroupIds/any(g: g eq '<group_id_1>' OR g eq '<group_id_2>'))`

4. **Result Trimming**
   - Only returns documents where the user has access
   - Security trimming happens at query execution time
   - Transparent to the application - looks like a normal search response

## Advantages Over Application-Level Filtering

### Application-Level Filtering (Manual OData)
```python
# OLD APPROACH - Manual filter construction
if user_groups:
    group_filters = " or ".join([f"g eq '{group}'" for group in user_groups])
    filter_parts.append(f"GroupIds/any(g: {group_filters})")

if user_oid:
    filter_parts.append(f"UserIds/any(u: u eq '{user_oid}')")

security_filter = " or ".join([f"({part})" for part in filter_parts])
payload["filter"] = security_filter
```

**Issues:**
- Application must extract and validate claims
- Must build OData filter syntax correctly
- Vulnerable to injection if not properly escaped
- Requires understanding of OData syntax

### Query-Time Access Control (Azure Native)
```python
# NEW APPROACH - Let Azure handle it
headers = {
    "Authorization": f"Bearer {search_access_token}",
    "x-ms-query-source-authorization": search_access_token,
    "Content-Type": "application/json"
}
# No filter construction needed!
```

**Benefits:**
- ✅ Azure validates and evaluates token
- ✅ No manual filter construction
- ✅ No injection risk
- ✅ Centralized security logic in Azure
- ✅ Consistent behavior across applications
- ✅ Easier to audit and maintain

## Testing

### Successful Search Request

**Python API Log:**
```
Unified search endpoint called with mode: OBO
User: admin@MngEnvMCAP536603.onmicrosoft.com (OID: 590cc83d-d461-4a20-9cc1-f3f631e88366)
Groups from incoming token: 0, Query: *
Using OBO authentication for AI Search
Calling AI Search with OBO Flow with Query-Time Access Control
Access control: Query-time access control: Azure AI Search evaluates GroupIds/UserIds based on user's token
Search URL: https://<YOUR_SEARCH_SERVICE>.search.windows.net/indexes/<YOUR_INDEX_NAME>/docs/search?api-version=2025-11-01-preview
AI Search response status: 200
```

### Verification Steps

1. **Sign in** to the React app with a user account
2. **Search** for documents (try `*` for all, or specific terms)
3. **Verify** results are filtered based on:
   - User's OID in document `UserIds`
   - User's groups in document `GroupIds`
4. **Check logs** in Python terminal for OBO success
5. **Compare** with different users to see different results

## Troubleshooting

### Error: "Audience claim is invalid in the JWT token"

**Problem:** Using the wrong token in `x-ms-query-source-authorization` header

**Solution:** Use the OBO token (for Search), not the incoming token (for API)
```python
# CORRECT
"x-ms-query-source-authorization": search_access_token

# WRONG
"x-ms-query-source-authorization": user_access_token
```

### Error: "Invalid_grant" during OBO

**Problem:** Azure AD permission not configured or consented

**Solution:**
1. Add Azure Search API permission in Azure Portal
2. Grant admin consent
3. Or use fallback: `SEARCH_AUTH_MODE=API_KEY`

### Error: 403 Forbidden

**Problem:** User lacks RBAC role on search service

**Solution:** Assign "Search Index Data Reader" role to user

### No Results Returned

**Problem:** User's OID/groups not in any document's `UserIds`/`GroupIds`

**Solution:**
1. Verify user's OID with `Request Access Token` button
2. Check document ACLs in search index
3. Add user's OID to document `UserIds` field

## Security Considerations

### Token Audience Validation

The token in `x-ms-query-source-authorization` must have:
- **Audience (aud):** Azure Search service or `https://search.azure.com`
- **Issuer (iss):** Entra ID tenant authority
- **Not expired:** Check `exp` claim

### Claims Required

For proper security filtering, the token should contain:
- **`oid`** (Object ID) - Always present for user tokens
- **`groups`** (optional) - Group memberships, requires configuration

### Defense in Depth

1. **Authentication:** Entra ID validates user identity
2. **Authorization:** OBO ensures proper token exchange
3. **Access Control:** Azure Search evaluates permissions
4. **Data Security:** Only authorized documents returned
5. **Transport Security:** HTTPS for all requests

## Configuration Summary

### Environment Variables
```bash
# Azure AD
CLIENT_ID=<YOUR_API_CLIENT_ID>
CLIENT_SECRET=<YOUR_CLIENT_SECRET>
TENANT_ID=<YOUR_TENANT_ID>

# Azure AI Search
SEARCH_ENDPOINT=https://<YOUR_SEARCH_SERVICE>.search.windows.net
SEARCH_INDEX=<YOUR_INDEX_NAME>
SEARCH_AUTH_MODE=OBO  # Default mode
SEARCH_API_KEY=<YOUR_SEARCH_API_KEY>  # Fallback
```

### Required Azure AD Permissions

**Python API App Registration:**
1. **Delegated Permission:** `https://search.azure.com/user_impersonation`
2. **Admin consent:** Required
3. **Exposed API:** `api://<YOUR_API_CLIENT_ID>/access_as_user` (configured in `config.py`)

**React SPA App Registration:**
1. **API Permission:** `api://<YOUR_API_CLIENT_ID>/access_as_user` (configured in `config.js`)

**Setup Guide:** See [Python API README - Azure AI Search Configuration](../msal-react-obo-sample/python-obo-api/README.md#azure-ai-search-configuration) for detailed setup instructions.

## Direct API Example

If testing with curl or Postman:

```bash
POST https://<YOUR_SEARCH_SERVICE>.search.windows.net/indexes/<YOUR_INDEX_NAME>/docs/search?api-version=2025-11-01-preview
Authorization: Bearer <search_access_token>
x-ms-query-source-authorization: <search_access_token>
Content-Type: application/json

{
    "search": "*",
    "select": "name,description,location,GroupIds,UserIds",
    "orderby": "name asc"
}
```

## References

- [Azure AI Search Query-Time Security Trimming](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search)
- [On-Behalf-Of (OBO) Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow)
- [Azure AI Search REST API](https://learn.microsoft.com/en-us/rest/api/searchservice/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)

## Status

✅ **Implemented and working** as of November 23, 2025
- OBO flow successful
- Query-time access control active
- Results properly filtered by user permissions
- React app displaying park names, descriptions, and locations
