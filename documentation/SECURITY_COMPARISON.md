# Security Comparison: OBO Flow vs API Key Authentication

## Overview

This document explains the security differences between using **On-Behalf-Of (OBO) Flow** and **API Key** authentication when accessing Azure AI Search from a middle-tier API.

> **Current Implementation:** This project uses **query-time access control** where Azure AI Search automatically filters results based on the user's token. See [QUERY-TIME_ACCESS_CONTROL.md](QUERY-TIME_ACCESS_CONTROL.md) for technical details.

> **Configuration:** Authentication mode is configurable via `SEARCH_AUTH_MODE` environment variable. See [Python API README](../msal-react-obo-sample/python-obo-api/README.md#authentication-modes) for setup instructions.

---

## Authentication Methods

### 1. On-Behalf-Of (OBO) Flow

**How it works:**
```
User → React SPA → Python API → Azure AI Search
 (User Token) → (Exchange to Search Token) → (User's Identity)
```

The OBO flow exchanges the user's token for a new token scoped to Azure AI Search, maintaining the **user's identity** throughout the call chain.

**Configuration:**
- Requires Azure AD app permissions
- Requires RBAC role assignment to **end users**
- Uses delegated permissions
- Token audience: `https://search.azure.com`
- Uses `x-ms-query-source-authorization` header for query-time access control
- API version: `2025-11-01-preview`

### 2. API Key Authentication

**How it works:**
```
User → React SPA → Python API → Azure AI Search
 (User Token) → (Extract User Info) → (Service Identity)
```

The Python API uses a **shared API key** to authenticate to Azure AI Search. The service acts on behalf of all users using the same credential.

**Configuration:**
- API key stored in `config.py` or `SEARCH_API_KEY` environment variable
- Recommended: Use Azure Key Vault for production
- No Azure AD permissions needed
- No user RBAC assignment needed
- Uses admin or query key from Azure Search

---

## Security Differences

| Aspect | OBO Flow | API Key |
|--------|----------|---------|
| **Identity Context** | User's identity preserved | Service identity (shared credential) |
| **RBAC Requirements** | Each user needs Search Index Data Reader role | Only API needs access (via key) |
| **Audit Logging** | Shows actual user performing search | Shows API service performing all searches |
| **Token Scope** | Scoped to specific user + resource | Full access to all operations allowed by key type |
| **Credential Management** | Azure AD manages tokens (auto-rotation) | Manual key rotation required |
| **Permission Model** | Azure AD delegated permissions | Shared secret |
| **Revocation** | Revoke user's Azure AD access | Revoke/regenerate entire key |
| **Least Privilege** | Users get only their assigned roles | API key has broad permissions |

---

## Security Implications

### OBO Flow (More Secure)

✅ **Advantages:**
- **True user context**: Every search request is made as the actual user
- **Individual accountability**: Audit logs show which user performed each search
- **Granular access control**: Different users can have different permissions
- **No shared secrets**: No API keys to protect, rotate, or leak
- **Automatic token expiration**: Tokens are short-lived (1 hour)
- **Centralized revocation**: Disable user in Azure AD = instant revocation
- **Zero Trust alignment**: Maintains identity throughout the request chain

❌ **Challenges:**
- **Complex setup**: Requires Azure AD app permissions and consent
- **User RBAC management**: Each user needs role assignment on search service
- **More configuration**: API permissions, role assignments, consent flow
- **Potential 403 errors**: If user lacks proper role assignment

### API Key (Less Secure, Easier Setup)

✅ **Advantages:**
- **Simple setup**: Just copy API key from portal
- **No user management**: No need to assign roles to every user
- **Quick to implement**: Works immediately
- **No Azure AD dependencies**: Works even with AAD issues

❌ **Security Concerns:**
- **Shared credential**: Same key used for all users
- **Lost user context**: Can't tell which user performed which action
- **Broad permissions**: Query keys allow access to all readable indexes
- **Credential exposure risk**: Key could be logged, cached, or leaked
- **Difficult revocation**: Revoking key affects all users
- **No automatic expiration**: Keys don't expire unless manually rotated
- **Compliance issues**: May not meet audit requirements

---

## Query-Time Security Filtering

**Important:** This implementation uses **Azure AI Search query-time access control** where the search service automatically handles security filtering based on the user's token.

### How Query-Time Access Control Works

```python
# OBO Mode: Pass search token in special header
headers = {
    "Authorization": f"Bearer {search_access_token}",
    "x-ms-query-source-authorization": search_access_token,
    "Content-Type": "application/json"
}

# Azure AI Search extracts from token:
# - User's OID (Object ID)
# - User's group memberships
# 
# Then automatically filters documents where:
# - UserIds collection contains user's OID, OR
# - GroupIds collection contains user's group IDs
#
# No manual filter construction needed!
```

### How Security Works in Each Method

#### OBO Flow:
1. User authenticates to React app
2. React acquires token for Python API
3. Python API uses OBO to get Azure Search token (as user)
4. Python API passes token in `x-ms-query-source-authorization` header
5. **Azure AI Search evaluates token and filters automatically**
6. Azure Search logs show actual user
7. RBAC enforces what user can access
8. Query-time filtering by UserIds/GroupIds from token

#### API Key:
1. User authenticates to React app
2. React acquires token for Python API
3. Python API uses API key (as service)
4. Python API sends request with api-key header
5. **Azure AI Search uses same query-time access control**
6. Azure Search logs show API service (not individual user)
7. API key has broad access (limited by key type)
8. Query-time filtering still applies based on token

---

## Comparison Examples

### Scenario: User "Alice" searches for "London"

**OBO Flow:**
```
React: Alice signs in → Gets token (OID: abc-123, Groups: [Group-A, Group-B])
Python: Receives Alice's token → OBO to Azure Search (still as Alice)
Python: Passes search token in x-ms-query-source-authorization header
Search: Azure extracts OID + groups from token
Search: Auto-filters where (UserIds contains 'abc-123') OR (GroupIds contains Group-A or Group-B)
Audit: "User: alice@contoso.com searched 'London'"
Result: Only documents Alice is authorized to see
```

**API Key:**
```
React: Alice signs in → Gets token (OID: abc-123, Groups: [Group-A, Group-B])
Python: Receives Alice's token → Uses API key (as service)
Python: Still passes token in x-ms-query-source-authorization header
Search: Azure extracts OID + groups from token
Search: Auto-filters where (UserIds contains 'abc-123') OR (GroupIds contains Group-A or Group-B)
Audit: "Service: Python-API searched 'London'" (loses individual user identity)
Result: Same filtering as OBO, but audit shows service not user
```

### Scenario: Malicious actor gets API key

**OBO Flow:**
```
Attacker: Has API key but no user token
Impact: Cannot call search (needs valid user token for OBO)
Risk: Minimal - still need to authenticate as valid user
```

**API Key:**
```
Attacker: Has API key from leaked environment variable
Impact: Can directly call Azure Search with full query key permissions
Risk: HIGH - can search all indexes, bypass all filtering
```

---

## Compliance Considerations

### OBO Flow Meets Requirements For:
- ✅ **SOC 2**: Individual user accountability
- ✅ **HIPAA**: Audit trail of who accessed what
- ✅ **GDPR**: User-level access tracking
- ✅ **Zero Trust**: Verify identity at every layer
- ✅ **Least Privilege**: Users get minimum necessary access

### API Key May NOT Meet:
- ❌ **Individual accountability**: Can't prove which user did what
- ❌ **Audit requirements**: Logs show service, not user
- ❌ **Credential rotation policies**: Manual rotation required
- ❌ **Principle of least privilege**: Shared credential with broad access

---

## Recommendations

### Use OBO Flow When:
- ✅ You need individual user accountability in audit logs
- ✅ Compliance requires user-level access tracking
- ✅ Different users should have different search permissions
- ✅ You want true Zero Trust architecture
- ✅ Production workloads with sensitive data
- ✅ You can manage Azure AD permissions and RBAC

### Use API Key When:
- ✅ Development, testing, or proof-of-concept scenarios
- ✅ Quick prototyping without Azure AD complexity
- ✅ All users should have same access level
- ✅ Azure AD permission configuration is blocked/difficult
- ✅ Audit requirements allow service-level logging
- ✅ You can secure the API key properly (Key Vault, rotation)

---

## Best Practices

### For OBO Flow:
1. **Assign roles per user/group**: Use Azure AD groups for easier management
2. **Monitor consent**: Ensure admin consent is granted for API permissions
3. **Handle 403 errors gracefully**: User may lack RBAC, provide clear error messages
4. **Token caching**: MSAL handles this automatically
5. **Scope validation**: Verify incoming token has correct scope for your API

### For API Key:
1. **Store in Key Vault**: Never hardcode in source code
2. **Use query keys**: Don't use admin keys in production
3. **Rotate regularly**: Set up automated key rotation
4. **Restrict IP ranges**: Use Azure Search firewall rules
5. **Pass user token**: Include `x-ms-query-source-authorization` header for query-time filtering
6. **Log user context**: Capture user identity from incoming token for your own logs
7. **Note limitation**: Azure Search audit logs show service, not individual users

### For Both Methods:
1. **Always apply security filters**: Don't rely solely on authentication
2. **Validate incoming tokens**: Check audience, issuer, signature
3. **Use HTTPS only**: Protect tokens and keys in transit
4. **Implement rate limiting**: Prevent abuse
5. **Monitor and alert**: Track unusual search patterns

---

## Current Implementation

This project demonstrates **both approaches**:

### Switch Between Modes:
```python
# In app.py
SEARCH_AUTH_MODE = os.environ.get("SEARCH_AUTH_MODE", "API_KEY")
```

**Set via environment variable:**
```powershell
# Use OBO (requires Azure AD permission + user RBAC)
$env:SEARCH_AUTH_MODE="OBO"

# Use API Key (requires only API key)
$env:SEARCH_AUTH_MODE="API_KEY"
```

### Status:
- ✅ **Microsoft Graph OBO**: Fully working
- ✅ **Azure Search API Key**: Fully working with query-time access control
- ✅ **Azure Search OBO**: Fully working with query-time access control
  - Token exchange: Working
  - Search query: Working (using `x-ms-query-source-authorization` header)
  - Index: `<YOUR_INDEX_NAME>`
  - API Version: `2025-11-01-preview`

---

## Conclusion

**OBO Flow** is the **more secure** approach that provides true user-level access control, individual accountability, and meets compliance requirements. It's the recommended approach for production workloads.

**API Key** is **simpler to set up** but has significant security limitations. It's acceptable for development/testing but should be carefully evaluated for production use.

**Both methods** use Azure AI Search's native **query-time access control** to automatically filter results based on UserIds and GroupIds. The key difference is:
- **OBO**: Audit logs show individual users + RBAC enforced
- **API Key**: Audit logs show service + no user RBAC

The ideal architecture uses **OBO flow** with **query-time access control** to provide:
- Defense-in-depth security
- Individual user accountability
- Automatic security filtering by Azure AI Search
- No manual filter construction vulnerability
