# Python OBO API

A Flask-based middle-tier API demonstrating the On-Behalf-Of (OBO) flow with integrations to Microsoft Graph and Azure AI Search. This API shows how to maintain user context while calling downstream services.

## Quick Start

1. **Configure the application:**
   - Update `config.py` with your Azure AD and Azure AI Search settings
   - See [CONFIGURATION.md](../CONFIGURATION.md) for detailed configuration guide

2. **Install dependencies:**
```powershell
pip install flask flask-cors msal PyJWT requests python-dotenv
```

3. **Configure authentication mode** (optional):
```powershell
# OBO mode (default - recommended for production)
$env:SEARCH_AUTH_MODE="OBO"

# OR API Key mode (for quick testing)
$env:SEARCH_AUTH_MODE="API_KEY"
```

4. **Run the API:**
```powershell
python app.py
```

The API starts on **http://localhost:5000**

## Dependencies

**Required Python Packages:**
- flask==3.0.0
- flask-cors==4.0.0
- msal==1.26.0
- PyJWT==2.8.0
- requests==2.31.0
- python-dotenv==1.0.0

**Python Version:** 3.8 or higher

## Architecture

```
React SPA (MSAL Browser)
    ↓ [Access Token]
Python API (MSAL Python)
    ↓ [OBO Token Exchange]
    ├─→ Microsoft Graph API
    └─→ Azure AI Search
```

## How OBO Works

### Microsoft Graph Flow
1. React SPA acquires access token (scope: `api://<YOUR_API_CLIENT_ID>/access_as_user`)
2. React SPA calls Python API with token in Authorization header
3. Python API validates token and extracts user claims
4. Python API uses OBO to exchange token for Microsoft Graph token
5. Python API calls Graph `/me` and `/me/memberOf` endpoints
6. Python API returns user info with group memberships

### Azure AI Search Flow
1. React SPA sends search query with access token
2. Python API either:
   - **OBO Mode** (default): Exchanges token for Azure Search token
   - **API Key Mode**: Uses service-level API key
3. Python API passes token in `x-ms-query-source-authorization` header
4. Azure AI Search automatically extracts user's OID and group memberships from token
5. Azure AI Search natively filters results where:
   - `UserIds` contains user's OID, OR
   - `GroupIds` contains any of user's groups
6. No manual filter construction needed - Azure handles security automatically

## Configuration

All configuration is centralized in `config.py`. See **[CONFIGURATION.md](../CONFIGURATION.md)** for the complete setup guide.

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **CLIENT_ID** | Python API client ID | `<YOUR_API_CLIENT_ID>` |
| **TENANT_ID** | Azure AD tenant ID | `<YOUR_TENANT_ID>` |
| **CLIENT_SECRET** | API client secret | Set in config.py or env variable |
| **SEARCH_ENDPOINT** | Azure AI Search endpoint | `https://<YOUR_SEARCH_SERVICE>.search.windows.net` |
| **SEARCH_INDEX** | Search index name | `<YOUR_INDEX_NAME>` |
| **SEARCH_AUTH_MODE** | Auth mode: `OBO` or `API_KEY` | `OBO` (default) |
| **SEARCH_API_KEY** | API key (for API_KEY mode) | Optional - set in env variable |

### Environment Variables

```powershell
# Authentication mode (optional - defaults to OBO)
$env:SEARCH_AUTH_MODE="OBO"        # Use On-Behalf-Of flow (recommended)
$env:SEARCH_AUTH_MODE="API_KEY"    # Use API key authentication

# API key (required only for API_KEY mode)
$env:SEARCH_API_KEY="your-key-here"
```

## API Endpoints

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Python OBO API is running"
}
```

### `POST /api/hello`
Demonstrates OBO flow with Microsoft Graph.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "message": "Hello World from Python OBO API!",
  "obo_flow": "Successful",
  "user_info": {
    "displayName": "John Doe",
    "userPrincipalName": "john@contoso.com",
    "id": "..."
  },
  "groups": ["Group 1", "Group 2"],
  "incoming_token_info": { ... },
  "graph_token_info": { ... }
}
```

### `POST /api/search`
Azure AI Search with OBO authentication (may fail without proper Azure config).

**Headers:**
- `Authorization: Bearer <access_token>`

**Body:**
```json
{
  "query": "search terms"
}
```

### `POST /api/search-simple`
Azure AI Search with API key authentication (always works).

**Headers:**
- `Authorization: Bearer <access_token>`

**Body:**
```json
{
  "query": "search terms"
}
```

### `POST /api/search-unified`
**Recommended:** Unified search endpoint that uses configured authentication mode.

**Headers:**
- `Authorization: Bearer <access_token>`

**Body:**
```json
{
  "query": "search terms"
}
```

**Response:**
```json
{
  "message": "AI Search completed successfully",
  "authentication": "OBO Flow",
  "flow": "React SPA -> Python API (OBO) -> Azure AI Search",
  "user_context": {
    "oid": "...",
    "upn": "user@contoso.com",
    "groups": ["guid1", "guid2"],
    "group_count": 2
  },
  "security_filtering": {
    "filter": "Query-time access control: Azure AI Search evaluates GroupIds/UserIds based on user's token",
    "description": "Azure AI Search automatically filters where UserIds contains user OID or GroupIds contains user groups"
  },
  "search_query": "search terms",
  "result_count": 5,
  "results": [ ... ],
  "incoming_token_info": { ... },
  "search_token_info": { ... }
}
```

## Security Features

### Token Validation
- Validates JWT signature and claims
- Verifies issuer, audience, and tenant
- Checks token expiration
- Extracts user identity (OID, UPN)

### Query-Time Access Control (Azure AI Search)
- No manual filter construction - Azure handles it natively
- Token passed in `x-ms-query-source-authorization` header
- Azure AI Search extracts user's OID and group memberships from token
- Documents filtered where `UserIds` contains user OID OR `GroupIds` contains user groups
- API version `2025-11-01-preview` required
- See [AI Search Query-Time Security Trimming.md](../../../AI%20Search%20Query-Time%20Security%20Trimming.md)

### Token Comparison
- Shows incoming access token claims
- Shows OBO-acquired token claims
- Demonstrates token scoping differences
- Educational feature for understanding OAuth flows

## Authentication Modes

The API supports two modes for Azure AI Search authentication:

| Feature | OBO Mode (Default) | API Key Mode |
|---------|-------------------|--------------|
| **Use Case** | Production with user context | Quick testing/demos |
| **User Identity** | Preserved throughout | Service identity only |
| **Audit Trail** | User-level tracking | Service account only |
| **Setup** | Requires Azure AD permissions + RBAC | Requires API key only |
| **Security** | Token-based (short-lived) | Key-based (long-lived) |
| **Compliance** | SOC 2, HIPAA, GDPR ready | Limited audit trail |
| **Query Filtering** | Azure AI Search evaluates user token | Azure AI Search evaluates user token |

Both modes use **query-time access control** - Azure AI Search automatically filters results based on the user's OID and group memberships from the token.

## Troubleshooting

### OBO Mode Issues (Default)

**Error: invalid_grant / AADSTS65001**
- **Cause**: Azure AD API permission not configured or not consented
- **Solution**: Add the `https://search.azure.com/user_impersonation` permission via Azure CLI and grant admin consent
- **Workaround**: Switch to API Key mode: `$env:SEARCH_AUTH_MODE="API_KEY"`
- **Status**: ✅ RESOLVED - Permission configured and consented

**Error: 403 Forbidden from Azure Search**
- **Cause**: User doesn't have "Search Index Data Reader" RBAC role
- **Solution**: Assign the role via Azure Portal IAM or Azure CLI (see configuration steps above)
- **Verification**: `az role assignment list --assignee user@contoso.com`
- **Note**: Wait 5-10 minutes for RBAC propagation
- **Workaround**: Switch to API Key mode (uses service principal credentials)

**Error: AADSTS500011**
- **Cause**: Azure doesn't recognize the resource principal
- **Solution**: Verify the correct tenant and resource endpoint
- **Workaround**: Use API_KEY mode

**Error: No authorization token**
- **Cause**: React app not sending token
- **Solution**: Ensure user is signed in and token is acquired via MSAL

**Error: No groups in token**
- **Expected behavior** - Groups queried via `/me/memberOf`
- OBO tokens are resource-specific
- Query-time access control handles this automatically

### API Key Mode Issues

**Error: SEARCH_API_KEY not configured**
- **Cause**: API key environment variable not set and hardcoded key removed
- **Solution**: Set `SEARCH_API_KEY` environment variable with valid key

**Error: 401 Unauthorized from Azure Search**
- **Cause**: Invalid or expired API key
- **Solution**: Get new key from Azure Portal → AI Search → Keys → Manage Keys
- **Via CLI**: `az search admin-key show --service-name <YOUR_SEARCH_SERVICE> --resource-group {resource-group}`

**Error: 403 Forbidden even with valid key**
- **Cause**: IP address not allowed
- **Solution**: Check Azure Search firewall rules, add your IP to allowed list, or disable firewall for testing

### General Issues

**Error: Token expired**
- **Solution**: MSAL automatically handles token refresh; sign out and sign in again if needed
- **Check**: Verify system clock is correct

**Error: Signature verification failed**
- **Cause**: Token may be tampered or corrupted
- **Solution**: Acquire new token, verify token is for correct audience

**Module resolution errors after directory restructure**
- **Cause**: MSAL packages not installed locally in React app
- **Solution**: 
  ```powershell
  cd demo\msal-react-obo-sample\msaljs-react-authflows-demo
  npm install @azure/msal-browser @azure/msal-react
  ```

**Python API not starting**
- Verify Python 3.8+ is installed
- Check port 5000 is not in use
- Install dependencies: `pip install flask flask-cors msal PyJWT requests python-dotenv`

---

## Azure AI Search Configuration

### Setup for OBO Mode (Default)

To use OBO mode, configure these Azure AD permissions:

#### 1. Add Azure Search API Permission

The Azure Search API permission is not available in the Azure Portal UI. Use Azure CLI:

```powershell
# Add Azure Search permission
az ad app permission add --id <YOUR_API_CLIENT_ID> `
  --api https://search.azure.com `
  --api-permissions user_impersonation=Scope

# Grant Admin Consent
az ad app permission admin-consent --id <YOUR_API_CLIENT_ID>
```

#### 2. Assign RBAC Roles to Users

Users need the "Search Index Data Reader" role to query the search index.

**Via Azure Portal:**
1. Navigate to your Azure AI Search resource
2. Go to **Access Control (IAM)** → **Add role assignment**
3. Select **Search Index Data Reader** role
4. Assign to users or Azure AD groups

**Via Azure CLI:**
```powershell
# Assign to a user
az role assignment create --role "Search Index Data Reader" `
  --assignee user@contoso.com `
  --scope /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Search/searchServices/<YOUR_SEARCH_SERVICE>

# Assign to a group (recommended)
az role assignment create --role "Search Index Data Reader" `
  --assignee {group-object-id} `
  --scope /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Search/searchServices/<YOUR_SEARCH_SERVICE>
```

**Note:** RBAC changes can take 5-10 minutes to propagate.

### Query-Time Access Control

Both authentication modes use **query-time access control** - Azure AI Search natively filters results based on user identity:

**How It Works:**
1. Python API passes user token in `x-ms-query-source-authorization` header
2. Azure AI Search extracts user's OID and group memberships from token
3. Results filtered where `UserIds` contains user's OID OR `GroupIds` contains user's groups
4. No manual OData filter construction needed

**Example:**
```
User Token Contains:
  OID: 590cc83d-d461-4a20-9cc1-f3f631e88366
  Groups: [6227941e-886e-4776-ad26-b7426f336f5b, 608666ac-73c9-46f9-a8da-88efae075849]

Azure AI Search Automatically Returns Documents Where:
  (UserIds contains '590cc83d-d461-4a20-9cc1-f3f631e88366') OR
  (GroupIds contains '6227941e-886e-4776-ad26-b7426f336f5b') OR
  (GroupIds contains '608666ac-73c9-46f9-a8da-88efae075849')
```

**Requirements:**
- API version: `2025-11-01-preview`
- Index fields: `UserIds` and `GroupIds` (Collection of Edm.String)
- Header: `x-ms-query-source-authorization: <user_token>`

---

## Security Architecture

### Multi-Tier Authentication Flow

```
┌─────────────────┐
│  User Browser   │  1. Sign In (Authorization Code + PKCE)
└────────┬────────┘
         ↓
┌─────────────────────────────────────────┐
│  React SPA (localhost:3000)             │  2. Acquire Access Token
│  MSAL Browser - scope: access_as_user   │     (scope: api://<client-id>/access_as_user)
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Python API (localhost:5000)            │  3. Validate Token
│  - Validates incoming token             │  4. OBO Token Exchange OR API Key
│  - Extracts user identity & groups      │
└────────┬────────────────────────────────┘
         ↓
         ├─→ Microsoft Graph API          5. Call Downstream Services
         │   └─ /me, /me/memberOf             with User Context
         │
         └─→ Azure AI Search
             └─ Query with query-time filtering
```

### Token Validation & Security

**Incoming Token Validation:**
- JWT signature verification against Azure AD public keys
- Claims validation: audience (aud), issuer (iss), expiration (exp), tenant (tid)
- User identity extraction: OID, UPN for audit logging

**Security Best Practices:**

1. **Use OBO Flow in Production**
   - Maintains user identity throughout the call chain
   - Enables individual accountability and compliance (SOC 2, HIPAA, GDPR)
   - Provides per-user RBAC enforcement at each service level

2. **Secure Secret Management**
   - Store client secrets and API keys in Azure Key Vault
   - Never hardcode credentials in source code
   - Rotate secrets every 90 days

3. **RBAC via Groups**
   - Assign permissions to Azure AD groups, not individual users
   - Easier to manage at scale

4. **Defense in Depth**
   - OBO for identity propagation
   - Query-time access control for data filtering
   - Azure Search firewall rules
   - API rate limiting

5. **Monitoring & Compliance**
   - Enable Azure AD sign-in logs
   - Enable Azure Search diagnostic logs
   - Regular access reviews

**OBO vs API Key Comparison:**

| Aspect | OBO Mode | API Key Mode |
|--------|----------|--------------|
| User Identity | ✅ Preserved | ❌ Service account only |
| Audit Trail | ✅ Per-user logs | ⚠️ Service-level only |
| Compliance | ✅ SOC 2, HIPAA, GDPR ready | ⚠️ Limited audit trail |
| Token Lifetime | ✅ Short-lived (hours) | ⚠️ Long-lived (manual rotation) |
| Setup Complexity | Higher | Lower |
| **Recommendation** | **Production** | **Testing/demos only** |

---

## Related Documentation

- **[CONFIGURATION.md](../CONFIGURATION.md)** - Complete configuration guide for both React and Python apps
- **[AI Search Query-Time Security Trimming.md](../../../AI%20Search%20Query-Time%20Security%20Trimming.md)** - Detailed query-time access control implementation
- **[React App README](../msaljs-react-authflows-demo/README.md)** - Frontend documentation

## What This Demo Shows

- ✅ On-Behalf-Of (OBO) token exchange patterns
- ✅ Multi-resource token acquisition (Graph + Azure AI Search)
- ✅ Query-time access control with native Azure AI Search filtering
- ✅ Token validation and security best practices
- ✅ Dual authentication modes (OBO and API Key)
- ✅ User identity preservation across service boundaries
