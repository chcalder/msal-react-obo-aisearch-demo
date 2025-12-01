# MSAL React On-Behalf-Of (OBO) and AI Search Security Filtering Demo

A comprehensive demonstration of authentication and authorization flows using Microsoft Authentication Library (MSAL) with React, Python Flask, and Azure services.

## Overview

This project showcases:
- **React SPA** with MSAL Browser for user authentication
- **Python Flask API** implementing the On-Behalf-Of (OBO) flow
- **Microsoft Graph API** integration for user profiles and group memberships
- **Azure AI Search** with native query-time access control (no manual filter construction)
- **Token comparison** features for understanding OAuth token scoping

![Authorization Model](images/authZ-Model.jpg)


## Project Structure

```
msal-react-obo-demo/
└── msal-react-obo-sample/
    ├── msaljs-react-authflows-demo/    # React SPA
    │   ├── src/                        # React components and pages
    │   ├── public/                     # Static assets
    │   └── README.md                   # React app documentation
    │
    └── python-obo-api/                 # Python Flask API
        ├── app.py                      # Main API application
        ├── config.py                   # Centralized configuration
        ├── requirements.txt            # Python dependencies
        └── README.md                   # API documentation with Azure AI Search and Security sections
```

## Architecture

```
User Browser
    ↓ [Authorization Code + PKCE]
React SPA (localhost:3000)
    ↓ [Access Token]
Python API (localhost:5000)
    ├─ [OBO Token Exchange]
    ├─→ Microsoft Graph API (/me, /me/memberOf)
    └─→ Azure AI Search (query-time access control via x-ms-query-source-authorization)
```

## Quick Start

### Prerequisites
- Node.js 16+
- Python 3.8+
- Azure subscription with:
  - Microsoft Entra ID tenant
  - App registrations configured
  - Azure AI Search resource

### 1. Start the Python API

```bash
cd msal-react-obo-sample/python-obo-api
pip install -r requirements.txt
python app.py
```

API runs at **http://localhost:5000**

### 2. Start the React App

```bash
cd msal-react-obo-sample/msaljs-react-authflows-demo
npm install
npm start
```

App runs at **http://localhost:3000**

### 3. Sign In and Test

1. Open http://localhost:3000
2. Click **Sign In**
3. Authenticate with your Entra ID credentials
4. Test features:
   - View access token claims
   - Call OBO API to get Microsoft Graph data
   - Search Azure AI with security filtering
   - Compare token differences

## Key Features

### 🔐 Authentication & Authorization
- **Authorization Code Flow with PKCE** for secure SPA authentication
- **On-Behalf-Of (OBO) Flow** for middle-tier token exchange
- **Multi-tier security** with identity propagation

### 📊 Microsoft Graph Integration
- User profile retrieval (`/me`)
- Group membership queries (`/me/memberOf`)
- Token comparison showing incoming vs OBO tokens

### 🔍 Azure AI Search
- **Dual authentication modes**: OBO flow or API key
- **Native query-time access control** - Azure AI Search handles filtering automatically
- **No manual OData filter construction** - token passed in `x-ms-query-source-authorization` header
- Azure extracts user OID and groups from token
- Documents filtered where `UserIds` contains user OID OR `GroupIds` contains user groups
- API version `2025-11-01-preview` required

### 🛡️ Security Features
- JWT token validation
- Group-based authorization
- Defense-in-depth security model
- Comprehensive audit logging (OBO mode)

## Configuration

### Azure AD App Registrations

**React SPA:**
- Client ID: `<YOUR_REACT_CLIENT_ID>`
- Tenant: `<YOUR_TENANT_ID>`
- Redirect URI: `http://localhost:3000`

**Python API:**
- Client ID: `<YOUR_API_CLIENT_ID>`
- API Scope: `api://<YOUR_API_CLIENT_ID>/access_as_user`
- Permissions: Microsoft Graph, Azure Search

**Azure AI Search:**
- Endpoint: `https://<YOUR_SEARCH_SERVICE>.search.windows.net`
- Index: `<YOUR_INDEX_NAME>`
- API Version: `2025-11-01-preview` (required for query-time access control)
- Security Fields: `GroupIds`, `UserIds` (Collection of Edm.String)
- Content Fields: `name`, `description`, `location` (configure as needed)
- Auth Mode: OBO (default) or API Key (fallback)

### Centralized Configuration

All configuration values are centralized for easy management:

**React Configuration:** `msal-react-obo-sample/msaljs-react-authflows-demo/src/config.js`
- Azure AD settings (client ID, tenant ID, authority)
- Python API endpoints
- Microsoft Graph configuration
- Azure AI Search display settings

**Python Configuration:** `msal-react-obo-sample/python-obo-api/config.py`
- Azure AD settings (client ID, secret, tenant ID)
- Microsoft Graph API settings
- Azure AI Search configuration
- Server and query defaults

See **[CONFIGURATION.md](msal-react-obo-sample/CONFIGURATION.md)** for detailed configuration guide.

### Environment Variables

```bash
# Python API
SEARCH_AUTH_MODE=OBO           # or "API_KEY"
SEARCH_API_KEY=<your-key>      # Required for API_KEY mode
```

## Documentation

- **[Configuration Guide](msal-react-obo-sample/CONFIGURATION.md)** - Centralized configuration management
- **[React App README](msal-react-obo-sample/msaljs-react-authflows-demo/README.md)** - Frontend setup and usage
- **[Python API README](msal-react-obo-sample/python-obo-api/README.md)** - Backend API endpoints, Azure AI Search configuration, and security architecture
- **[Security Comparison](documentation/SECURITY_COMPARISON.md)** - OBO vs API Key detailed analysis
- **[Auth Flow Summary](documentation/AUTHFLOW_SUMMARY.md)** - End-to-end authentication flow
- **[Query-Time Access Control Guide](documentation/QUERY-TIME_ACCESS_CONTROL.md)** - Comprehensive query-time access control guide

## Authentication Flows

### Authorization Code Flow with PKCE (React → Azure AD)
1. User clicks sign-in
2. Redirected to Microsoft login
3. User authenticates
4. Authorization code returned
5. MSAL exchanges code for tokens (with PKCE)
6. User authenticated in React app

### On-Behalf-Of Flow (React → API → Graph/Search)
1. React acquires access token for API
2. React calls API with Bearer token
3. API validates incoming token
4. API exchanges token for downstream service token
5. API calls downstream service (Graph/Search)
6. Results returned to React

## Technology Stack

### Frontend
- React 19.1.0
- MSAL Browser 4.0.0
- MSAL React 3.0.0
- React Router DOM 6.7.0
- Material-UI 5.9.0

### Backend
- Python Flask 3.0.0
- MSAL Python 1.26.0
- flask-cors 4.0.0
- PyJWT 2.8.0
- requests 2.31.0

### Azure Services
- Microsoft Entra ID (Azure AD)
- Microsoft Graph API
- Azure AI Search

## Security Considerations

### OBO Flow (Recommended for Production)
✅ User identity preserved throughout call chain  
✅ Individual accountability in audit logs  
✅ Per-user RBAC enforcement  
✅ Zero Trust architecture alignment  
✅ Compliance-friendly (SOC 2, HIPAA, GDPR)

### API Key Mode (Good for Demos)
⚠️ Service-level authentication  
⚠️ Shared credential across users  
⚠️ Limited audit trail  
⚠️ Still applies query-time access control (passes same token to Azure AI Search)

See the [Python API README](msal-react-obo-sample/python-obo-api/README.md#security-architecture) for detailed security analysis.

## Troubleshooting

### Module Resolution Errors (React)
```bash
cd msal-react-obo-sample/msaljs-react-authflows-demo
npm install @azure/msal-browser @azure/msal-react
```

### OBO Flow Errors (Python API)
- **403 Forbidden**: User needs "Search Index Data Reader" RBAC role
  - Assign via Azure Portal: AI Search → Access Control (IAM) → Add role assignment
- **invalid_grant (RESOLVED)**: Was Azure AD permission issue, now fixed
  - `https://search.azure.com/user_impersonation` permission configured and consented
  - Status: ✅ OBO flow fully working
- **Workaround**: If issues persist, switch to API Key mode: `$env:SEARCH_AUTH_MODE="API_KEY"`

### CORS Errors
Ensure Python API is running and has CORS enabled for `http://localhost:3000`

## Resources

### MSAL Documentation
- [MSAL.js](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)

### Microsoft Identity Platform
- [Authorization Code Flow](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [On-Behalf-Of Flow](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow)
- [Microsoft Graph API](https://docs.microsoft.com/graph/overview)

### Azure Services
- [Azure AI Search](https://docs.microsoft.com/azure/search/)
- [Azure RBAC](https://docs.microsoft.com/azure/role-based-access-control/overview)

## Contributing

This is a demonstration project. Feel free to fork and adapt for your own use cases.

## License

MIT License - See individual component licenses for details.

## Author

Chris Calderon (chcalder@microsoft.com)

---

**Note**: This project contains pre-configured Azure AD app registrations and service endpoints for demonstration purposes. When deploying to production, create your own app registrations and follow security best practices.
