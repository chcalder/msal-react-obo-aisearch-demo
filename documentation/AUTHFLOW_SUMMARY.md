# Authentication Flow Code Summary

> **Note:** This implementation uses **query-time access control** for Azure AI Search. The search service automatically filters results based on user permissions extracted from the token via the `x-ms-query-source-authorization` header. See [AI Search Query-Time Security Trimming.md](AI%20Search%20Query-Time%20Security%20Trimming.md) for detailed implementation.

## 1. Initial Authentication to Entra ID (React SPA)

### **SignInButton.jsx** - Lines 14-22
```javascript
const handleLogin = (loginType) => {
    setAnchorEl(null);

    if (loginType === "popup") {
        instance.loginPopup(loginRequest);      // Line 18
    } else if (loginType === "redirect") {
        instance.loginRedirect(loginRequest);   // Line 20
    }
}
```
**Triggers:** Authorization Code Flow with PKCE to Entra ID

### **authConfig.js** - Lines 19-24
```javascript
export const msalConfig = {
    auth: {
        clientId: "<YOUR_REACT_CLIENT_ID>",
        authority: "https://login.microsoftonline.com/<YOUR_TENANT_ID>",
        redirectUri: "/",
        postLogoutRedirectUri: "/"
    }
}
```
**Configuration:** Defines Entra ID tenant and client ID (imports from `config.js`)

---

## 2. Access Token Acquisition (React SPA)

### **Home.jsx** - Line 71 (Request Access Token Button)
```javascript
instance.acquireTokenSilent({
    ...apiRequest,  // Scope: api://<YOUR_API_CLIENT_ID>/access_as_user
    account: account
}).then(response => {
    const claims = parseJwt(response.accessToken);
    setAccessTokenClaims(claims);
})
```
**Purpose:** Get token for Python API, display claims in UI

### **Home.jsx** - Line 100 (Call OBO API Button)
```javascript
const response = await instance.acquireTokenSilent({
    ...apiRequest,
    account: account
});

fetch('http://localhost:5000/api/hello', {
    headers: {
        'Authorization': `Bearer ${response.accessToken}`,
        'Content-Type': 'application/json'
    }
})
```
**Purpose:** Get token and call Python API for Microsoft Graph OBO

### **Home.jsx** - Line 139 (AI Search Button)
```javascript
const response = await instance.acquireTokenSilent({
    ...apiRequest,
    account: account
});

fetch('http://localhost:5000/api/search-unified', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${response.accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: searchQuery })
})
```
**Purpose:** Get token and call Python API for Azure AI Search

---

## 3. OBO Flow in Python API

### **app.py** - Lines 80-98 (Token Validation)
```python
@app.route('/api/hello', methods=['POST'])
def hello():
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1] if auth_header else None
    
    # Decode and validate incoming token
    token_decoded = jwt.decode(
        token,
        options={"verify_signature": False},
        algorithms=["RS256"]
    )
```
**Purpose:** Extract and validate incoming access token from React

### **app.py** - Lines 109-127 (OBO Token Exchange for Microsoft Graph)
```python
# Exchange user token for Microsoft Graph token using OBO
result = cca.acquire_token_on_behalf_of(
    user_assertion=token,
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    graph_token = result['access_token']
    
    # Call Microsoft Graph API
    graph_response = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': f'Bearer {graph_token}'}
    )
    
    # Get user groups
    groups_response = requests.get(
        'https://graph.microsoft.com/v1.0/me/memberOf',
        headers={'Authorization': f'Bearer {graph_token}'}
    )
```
**Flow:** User Token → OBO Exchange → Graph Token → Graph API Call

### **app.py** - Lines 440-460 (OBO Token Exchange for Azure AI Search)
```python
if SEARCH_AUTH_MODE == "OBO":
    # Exchange user token for Azure Search token using OBO
    result = msal_app.acquire_token_on_behalf_of(
        user_assertion=user_access_token,
        scopes=["https://search.azure.com/.default"]
    )
    
    if "access_token" in result:
        search_access_token = result['access_token']
        
        # Call Azure AI Search with query-time access control
        headers = {
            'Authorization': f'Bearer {search_access_token}',
            'x-ms-query-source-authorization': search_access_token,
            'Content-Type': 'application/json'
        }
        search_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version=2025-11-01-preview"
```
**Flow:** User Token → OBO Exchange → Search Token → Query-Time Access Control

### **app.py** - Lines 468-476 (API Key Mode - Alternative to OBO)
```python
else:
    # Use API key authentication instead of OBO
    if not SEARCH_API_KEY:
        return jsonify({"error": "SEARCH_API_KEY not configured"}), 500
    
    headers = {
        'api-key': SEARCH_API_KEY,
        'Content-Type': 'application/json'
    }
    auth_method = "API Key"
```
**Flow:** API Key Auth → Query-Time Access Control (no manual filter)

### **app.py** - Lines 37-42 (MSAL Configuration)
```python
cca = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET,
)
```
**Purpose:** Initialize MSAL for OBO token exchanges (values from `config.py`)

---

## 4. Query-Time Access Control (Python API)

### **app.py** - Lines 415-419 (Azure AI Search Evaluates Token)
```python
# Using query-time access control - Azure AI Search handles filtering based on token
# No manual filter construction needed
filter_description = "Query-time access control: Azure AI Search evaluates GroupIds/UserIds based on user's token"
```
**Purpose:** Azure AI Search automatically filters results based on user's OID and group memberships from the token

### How It Works:
1. User's OID and groups extracted from token by Azure AI Search
2. Documents filtered where `UserIds` contains user's OID OR `GroupIds` contains user's groups
3. No manual OData filter construction in application code
4. Uses `x-ms-query-source-authorization` header with preview API version

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Authentication (React → Entra ID)                       │
│    SignInButton.jsx: instance.loginPopup/loginRedirect()        │
│    Result: ID Token + Access Token (for React app)              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Token Acquisition (React SPA)                                │
│    Home.jsx: instance.acquireTokenSilent()                      │
│    Scope: api://<YOUR_API_CLIENT_ID>/access_as_user             │
│    Result: Access Token for Python API                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. API Call with Token (React → Python)                         │
│    Home.jsx: fetch('/api/hello' or '/api/search-unified')       │
│    Header: Authorization: Bearer <access_token>                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Token Validation (Python API)                                │
│    app.py: Extract token from Authorization header              │
│    app.py: jwt.decode() - validate and extract claims           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5a. OBO Flow - Microsoft Graph                                  │
│     app.py: cca.acquire_token_on_behalf_of()                    │
│     Scope: https://graph.microsoft.com/.default                 │
│     Result: Graph Access Token                                  │
│             ↓                                                    │
│     app.py: requests.get('https://graph.microsoft.com/v1.0/me') │
│     Result: User profile + groups                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 5b. OBO Flow - Azure AI Search (if SEARCH_AUTH_MODE=OBO)       │
│     app.py: msal_app.acquire_token_on_behalf_of()               │
│     Scope: https://search.azure.com/.default                    │
│     Result: Search Access Token                                 │
│             ↓                                                    │
│     app.py: Add x-ms-query-source-authorization header          │
│     app.py: requests.post(search_endpoint)                      │
│     Azure AI Search: Evaluates token, filters by GroupIds/UserIds │
│     Result: Filtered search results (query-time access control) │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 5c. API Key Flow - Azure AI Search (if SEARCH_AUTH_MODE=API_KEY)│
│     app.py: Use API key for authentication (no OBO)             │
│     app.py: requests.post(search_endpoint) with api-key header  │
│     Note: Still uses same query-time access control approach    │
│     Result: Filtered search results                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Files & Line Numbers Reference

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Initial Login** | SignInButton.jsx | 18, 20 | Trigger Entra ID login |
| **Token Acquisition** | Home.jsx | 71, 100, 139 | Get access tokens |
| **Token Validation** | app.py | 80-98 | Validate incoming token |
| **OBO - Graph** | app.py | 109-127 | Exchange for Graph token |
| **OBO - Search** | app.py | 440-460 | Exchange for Search token |
| **API Key - Search** | app.py | 468-476 | Use API key instead |
| **Query-Time Access Control** | app.py | 415-419, 457-460 | Azure evaluates token |
| **MSAL Config** | authConfig.js | 19-24 | Entra ID configuration (from config.js) |
| **MSAL Python** | app.py | 37-42 | OBO client setup (from config.py) |

---

## Authentication Patterns

### Pattern 1: Authorization Code Flow with PKCE
**Location:** React SPA → Entra ID  
**Purpose:** Initial user authentication  
**Result:** ID token + access token for SPA  
**Code:** `SignInButton.jsx` lines 18, 20

### Pattern 2: Token Acquisition
**Location:** React SPA  
**Purpose:** Get access token for Python API  
**Method:** `acquireTokenSilent()` - tries cache, then silent refresh  
**Code:** `Home.jsx` lines 71, 100, 139

### Pattern 3: On-Behalf-Of (OBO) Flow
**Location:** Python API  
**Purpose:** Exchange user's token for downstream service token  
**Method:** `acquire_token_on_behalf_of()`  
**Targets:** 
- Microsoft Graph API
- Azure AI Search  
**Code:** `app.py` lines 109-127 (Graph), 428-460 (Search)

### Pattern 4: API Key Authentication (Alternative)
**Location:** Python API  
**Purpose:** Service-level authentication when OBO not configured  
**Security:** Still applies user group filtering  
**Code:** `app.py` lines 465-485

---

## Token Scopes

### React SPA Requests
- **Scope:** `api://<YOUR_API_CLIENT_ID>/access_as_user`
- **Audience:** Python API
- **Contains:** User identity, groups (optional claim)

### Python API OBO - Microsoft Graph
- **Scope:** `https://graph.microsoft.com/.default`
- **Audience:** Microsoft Graph
- **Permissions:** User.Read, GroupMember.Read.All

### Python API OBO - Azure AI Search
- **Scope:** `https://search.azure.com/.default`
- **Audience:** Azure AI Search
- **Permissions:** user_impersonation

---

## Security Implementation

### Token Validation (app.py lines 80-98)
1. Extract token from Authorization header
2. Decode JWT (signature validation by MSAL)
3. Verify claims (issuer, audience, expiration)
4. Extract user identity (OID, UPN)

### Query-Time Access Control (app.py lines 415-419, 457-460)
1. OBO token passed in `x-ms-query-source-authorization` header
2. Azure AI Search extracts user OID and groups from token
3. Automatically filters documents where `UserIds` or `GroupIds` match
4. Users only see authorized documents
5. No manual filter construction needed

### Defense in Depth
- **Layer 1:** Entra ID authentication
- **Layer 2:** Token validation at API
- **Layer 3:** OBO token exchange (maintains identity)
- **Layer 4:** Group-based security filtering
- **Layer 5:** Azure RBAC (OBO mode only)

---

## Error Handling

### Common Scenarios

**Token Expired:**
- `acquireTokenSilent()` automatically refreshes
- Falls back to interactive login if needed

**OBO Permission Missing:**
- Error: `invalid_grant` or `AADSTS65001`
- Solution: Configure Azure AD permission, grant consent
- Fallback: Switch to API_KEY mode

**User Lacks RBAC Role:**
- Error: 403 Forbidden (OBO mode)
- Solution: Assign "Search Index Data Reader" role
- Fallback: Switch to API_KEY mode

**No Groups in Token:**
- Behavior: Query Graph API `/me/memberOf`
- Alternative: Configure groups as optional claim
- Search: Return all results if no groups

---

## Configuration Summary

### React App (src/config.js)
```javascript
clientId: "<YOUR_REACT_CLIENT_ID>"
authority: "https://login.microsoftonline.com/<YOUR_TENANT_ID>"
apiScope: "api://<YOUR_API_CLIENT_ID>/access_as_user"
```

### Python API (config.py)
```python
CLIENT_ID = "<YOUR_API_CLIENT_ID>"
TENANT_ID = "<YOUR_TENANT_ID>"
SEARCH_ENDPOINT = "https://<YOUR_SEARCH_SERVICE>.search.windows.net"
SEARCH_INDEX = "<YOUR_INDEX_NAME>"
SEARCH_AUTH_MODE = "OBO"  # or "API_KEY"
```

**Note:** All configuration values are centralized in `config.js` (React) and `config.py` (Python). See [CONFIGURATION.md](../msal-react-obo-sample/CONFIGURATION.md) for setup details.

---

## Testing the Flows

### Test 1: Initial Authentication
1. Open http://localhost:3000
2. Click "Sign In"
3. Authenticate with Entra ID credentials
4. Verify redirect back to app

### Test 2: Token Acquisition
1. Click "Request Access Token"
2. Verify token claims displayed
3. Check for OID, UPN, groups

### Test 3: OBO - Microsoft Graph
1. Click "Call OBO API"
2. Verify user profile displayed
3. Verify group memberships shown
4. Check token comparison

### Test 4: OBO - Azure AI Search
1. Enter search query
2. Click search button
3. Verify results filtered by groups
4. Check security filter applied

### Test 5: API Key Mode
1. Set `SEARCH_AUTH_MODE=API_KEY`
2. Restart Python API
3. Repeat search test
4. Verify still filters by groups

---

## Troubleshooting Guide

### React App Won't Compile
**Error:** Module not found: '@azure/msal-react'  
**Fix:**
```bash
cd msal-react-obo-sample/msaljs-react-authflows-demo
npm install @azure/msal-browser @azure/msal-react
```

### Python API OBO Fails
**Error:** invalid_grant  
**Check:**
1. Azure AD permission configured?
2. Admin consent granted?
3. Client secret valid?

**Workaround:**
```bash
$env:SEARCH_AUTH_MODE="API_KEY"
python app.py
```

### Search Returns 403
**Error:** 403 Forbidden  
**Cause:** User lacks RBAC role  
**Fix:** Assign "Search Index Data Reader" to user/group

### No Groups in Token
**Expected:** Groups queried via Graph API  
**Verify:** OBO response includes groups from `/me/memberOf`  
**Alternative:** Configure groups as optional claim in token

---

## Related Documentation

- **[README.md](../README.md)** - Project overview and quick start
- **[SECURITY_COMPARISON.md](SECURITY_COMPARISON.md)** - OBO vs API Key security analysis
- **[QUERY-TIME_ACCESS_CONTROL.md](QUERY-TIME_ACCESS_CONTROL.md)** - Azure AI Search query-time access control guide
- **[React App README](../msal-react-obo-sample/msaljs-react-authflows-demo/README.md)** - Frontend documentation
- **[Python API README](../msal-react-obo-sample/python-obo-api/README.md)** - Backend documentation with Azure AI Search and Security sections
- **[Configuration Guide](../msal-react-obo-sample/CONFIGURATION.md)** - Centralized configuration management
