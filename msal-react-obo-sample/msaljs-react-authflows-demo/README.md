# MSAL React Authentication Flows Demo

## About this sample

This React single-page application demonstrates advanced authentication and authorization patterns using MSAL React, including:

- **Authorization Code Flow with PKCE** - Secure authentication for SPAs
- **On-Behalf-Of (OBO) Flow** - Token exchange for middle-tier APIs
- **Microsoft Graph Integration** - User profile and group membership queries
- **Azure AI Search Integration** - Native query-time access control (no manual filter construction)
- **Token Comparison** - Educational feature showing token claim differences
- **Group-Based Authorization** - Role-based access control using Entra ID groups

This sample works in conjunction with the Python Flask API (`../python-obo-api/`) to demonstrate secure multi-tier authentication patterns.

This sample was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Architecture

```
User Browser
    ↓
React SPA (localhost:3000)
    ├─ MSAL Browser (Authorization Code + PKCE)
    ↓ [Access Token]
Python API (localhost:5000)
    ├─ MSAL Python (OBO Token Exchange)
    ↓
    ├─→ Microsoft Graph API
    │   ├─ /me (User Profile)
    │   └─ /me/memberOf (Group Memberships)
    │
    └─→ Azure AI Search
        └─ Query with Security Filtering
```

## Key Features

### 1. Token Acquisition & Display
- Acquire access tokens for Python API
- Display ID token and access token claims
- Show user identity information (OID, UPN, roles)

### 2. On-Behalf-Of (OBO) Flow Demo
- Exchange user token for Microsoft Graph token
- Retrieve user profile and group memberships
- Display OBO flow results with token comparison

### 3. Azure AI Search with Query-Time Access Control
- Query Azure AI Search with user context
- Azure AI Search automatically extracts user OID and group memberships from token
- Documents filtered where `UserIds` contains user OID OR `GroupIds` contains user groups
- No manual OData filter construction - Azure handles security natively
- Uses `x-ms-query-source-authorization` header with API version `2025-11-01-preview`
- Support for both OBO and API Key authentication modes

### 4. Token Comparison Feature
- Side-by-side comparison of incoming vs OBO tokens
- Educational feature showing token scoping
- Demonstrates resource-specific token claims

## Notable files and what they demonstrate

### Core Authentication
1. **`./src/index.js`** - Initializes `PublicClientApplication` with Entra ID configuration
1. **`./src/App.js`** - Implements `MsalProvider` context for all components
1. **`./src/config.js`** - Centralized configuration for Azure AD, API endpoints, and search settings
1. **`./src/authConfig.js`** - MSAL configuration that imports from `config.js`

### Pages
1. **`./src/pages/Home.jsx`** - Main authenticated page demonstrating:
   - Token acquisition and display
   - OBO flow with Microsoft Graph
   - Azure AI Search integration with security filtering
   - Token comparison UI
   - Conditional rendering with `AuthenticatedTemplate`/`UnauthenticatedTemplate`
1. **`./src/pages/Profile.jsx`** - Protected route example using `MsalAuthenticationTemplate`
1. **`./src/pages/Logout.jsx`** - Logout confirmation page

### UI Components
1. **`./src/ui-components/SignInSignOutButton.jsx`** - Conditional button using `useIsAuthenticated` hook
1. **`./src/ui-components/SignInButton.jsx`** - Sign-in button using `useMsal` hook
1. **`./src/ui-components/SignOutButton.jsx`** - Sign-out button using `useMsal` hook
1. **`./src/ui-components/AccountPicker.jsx`** - Account selection for multi-account scenarios
1. **`./src/ui-components/WelcomeName.jsx`** - Display authenticated user's name

### Utilities
1. **`./src/utils/NavigationClient.js`** - Custom navigation client for MSAL with React Router integration

## Prerequisites

- **Node.js 16+** and npm
- **Python 3.8+** (for the backend API)
- **Microsoft Entra ID tenant** with app registrations
- **Azure AI Search** resource (for search demos)

## Configuration

All application configuration is centralized in:
- **React App**: `./src/config.js` - Frontend configuration
- **Python API**: `../python-obo-api/config.py` - Backend configuration

See **[CONFIGURATION.md](../CONFIGURATION.md)** for the complete setup guide.

### Current Settings

| Component | Setting | Value |
|-----------|---------|-------|
| **React SPA** | Client ID | `<YOUR_REACT_CLIENT_ID>` |
| | Tenant ID | `<YOUR_TENANT_ID>` |
| | Redirect URI | `http://localhost:3000` |
| **Python API** | Client ID | `<YOUR_API_CLIENT_ID>` |
| | API Scope | `api://<YOUR_API_CLIENT_ID>/access_as_user` |
| | Endpoint | `http://localhost:5000` |
| **Azure AI Search** | Endpoint | `https://<YOUR_SEARCH_SERVICE>.search.windows.net` |
| | Index | `<YOUR_INDEX_NAME>` |
| | API Version | `2025-11-01-preview` |
| | Auth Mode | OBO (default) or API Key |

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

If you encounter module resolution errors after restructuring:
```bash
npm install @azure/msal-browser @azure/msal-react
```

### 2. Start the React App

```bash
npm start
```

The app will open at **http://localhost:3000**

### 3. Start the Python API

In a separate terminal:
```bash
cd ../python-obo-api
python app.py
```

The API will start at **http://localhost:5000**

### 4. Sign In and Test

1. Click **Sign In** button
2. Authenticate with your Entra ID credentials
3. On the home page, try:
   - **Request Access Token** - View your access token claims
   - **Call OBO API** - Test Microsoft Graph integration with groups
   - **Azure AI Search** - Search with security filtering

## App Registration Setup

This sample is pre-configured for demo purposes. To use your own Entra ID tenant:

### 1. Register the React SPA

1. Navigate to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations**
2. Click **New registration**
3. Configure:
   - **Name**: `MSAL React Auth Flows Demo`
   - **Supported account types**: Single tenant
   - **Redirect URI**: `Single-page application (SPA)` → `http://localhost:3000`
4. After registration, note the **Application (client) ID**
5. Under **Authentication**:
   - Add redirect URI: `http://localhost:3000`
   - Add logout URL: `http://localhost:3000`
   - Enable **Access tokens** and **ID tokens**

### 2. Register the Python API

1. Create another app registration for the API
2. Under **Expose an API**:
   - Set Application ID URI: `api://{client-id}`
   - Add scope: `access_as_user` with admin and user consent
3. Under **API permissions**:
   - Add Microsoft Graph: `User.Read`, `GroupMember.Read.All`
   - Add Azure Search: `user_impersonation` (if using OBO for search)
4. Create a **client secret** under **Certificates & secrets**

### 3. Configure the Applications

**React App** - Edit `./src/config.js`:
```javascript
export const AZURE_AD_CONFIG = {
  clientId: "YOUR_REACT_APP_CLIENT_ID",
  tenantId: "YOUR_TENANT_ID",
  // ... other settings
};
```

**Python API** - Edit `../python-obo-api/config.py`:
```python
"client_id": "YOUR_API_CLIENT_ID",
"tenant_id": "YOUR_TENANT_ID",
"client_secret": "YOUR_CLIENT_SECRET",
# ... other settings
```

See **[CONFIGURATION.md](../CONFIGURATION.md)** for complete configuration details.

## Using the Application

### Authentication
1. Click **Sign In** button in the top navigation
2. You'll be redirected to Microsoft sign-in page
3. Enter your Entra ID credentials
4. Grant consent for requested permissions
5. You'll be redirected back to the application

### Home Page Features

#### Request Access Token
- Displays your current access token claims
- Shows user identity (OID, UPN, name)
- Demonstrates token structure and claims

#### Call OBO API (Microsoft Graph)
- Exchanges your token for a Microsoft Graph token
- Retrieves your profile information
- Lists your group memberships
- Shows token comparison (incoming vs OBO token)

#### Azure AI Search
- Enter search terms to query the search index
- Azure AI Search automatically filters results based on your token
- Documents returned where `UserIds` contains your OID OR `GroupIds` contains your groups
- Shows query-time access control status and user context
- Displays park information: name, description, location

#### Compare Tokens
- Displays incoming access token and OBO token side-by-side
- Educational feature showing how token claims change
- Demonstrates resource-specific token scoping

### Profile Page
- Example of a protected route
- Automatically invokes sign-in if not authenticated
- Shows Microsoft Graph API call pattern

## Development

### Development Server
```bash
npm start
```
- Opens at [http://localhost:3000](http://localhost:3000)
- Hot reloading enabled
- Lint errors shown in console

### Production Build
```bash
npm run build
```

Serve production build:
```bash
npx serve -s build
```

### Available Scripts

- **`npm start`** - Start development server
- **`npm run build`** - Create production build
- **`npm test`** - Run tests
- **`npm run eject`** - Eject from Create React App (one-way operation)

## Technology Stack

### Core Libraries
- **React 19.1.0** - UI framework
- **MSAL Browser 4.0.0** - Browser authentication library
- **MSAL React 3.0.0** - React integration for MSAL
- **React Router DOM 6.7.0** - Client-side routing
- **Material-UI 5.9.0** - UI component library

### Backend Integration
- **Python Flask 3.0.0** - Middle-tier API
- **MSAL Python 1.26.0** - Server-side OBO flow
- **Microsoft Graph API** - User and directory data
- **Azure AI Search** - Intelligent search with security

## Troubleshooting

### Module Resolution Errors
If you see "Can't resolve '@azure/msal-react'" or similar:
```bash
npm install @azure/msal-browser @azure/msal-react
```

### Port Already in Use
If port 3000 is in use:
```bash
# Windows
$env:PORT=3001; npm start

# Linux/Mac
PORT=3001 npm start
```

### CORS Errors
Ensure the Python API is running on `http://localhost:5000` and has CORS enabled for `http://localhost:3000`.

### Authentication Errors
- **AADSTS50011**: Reply URL mismatch - Verify redirect URI is `http://localhost:3000`
- **AADSTS65001**: User consent required - Grant permissions in Azure Portal
- **Invalid token**: Ensure you're using the correct tenant and client IDs

### Azure AI Search Errors
- **403 Forbidden**: User needs "Search Index Data Reader" RBAC role
  - Assign via Azure Portal: AI Search → Access Control (IAM) → Add role assignment
  - See [Python API README - Azure AI Search Configuration](../python-obo-api/README.md#azure-ai-search-configuration) for detailed setup
- **OBO Token Exchange Failed**: Verify Azure AD permissions are configured
  - Permission required: `https://search.azure.com/user_impersonation`
  - Use Azure CLI to add permission and grant admin consent
- **Fallback Option**: Switch Python API to API Key mode for testing
  - Set environment variable: `$env:SEARCH_AUTH_MODE="API_KEY"`
  - See [Python API README - Authentication Modes](../python-obo-api/README.md#authentication-modes)

## Related Documentation

- **[Python API README](../python-obo-api/README.md)** - Complete backend documentation with Azure AI Search and security configuration
- **[CONFIGURATION.md](../CONFIGURATION.md)** - Centralized configuration guide for both React and Python apps
- **[Query-Time Access Control](../../../AI%20Search%20Query-Time%20Security%20Trimming.md)** - Detailed implementation guide
- **[Auth Flow Summary](../../../documentation/AUTHFLOW_SUMMARY.md)** - End-to-end authentication flow walkthrough
- **[Security Comparison](../../../documentation/SECURITY_COMPARISON.md)** - OBO vs API Key analysis
- **[Demo README](../../../README.md)** - Overall project documentation

## Learn More

### MSAL Resources
- [MSAL React Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js/tree/dev/lib/msal-react)
- [MSAL Browser Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js/tree/dev/lib/msal-browser)
- [MSAL.js Samples](https://github.com/AzureAD/microsoft-authentication-library-for-js/tree/dev/samples)

### Microsoft Identity Platform
- [Authorization Code Flow with PKCE](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [On-Behalf-Of Flow](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow)
- [Microsoft Entra ID Documentation](https://docs.microsoft.com/azure/active-directory/develop/)
- [Microsoft Graph API](https://docs.microsoft.com/graph/overview)

### Framework Documentation
- [React Documentation](https://react.dev)
- [Create React App Documentation](https://create-react-app.dev)
- [React Router Documentation](https://reactrouter.com)
- [Material-UI Documentation](https://mui.com/material-ui/getting-started/)

## License

This project is licensed under the MIT License.
