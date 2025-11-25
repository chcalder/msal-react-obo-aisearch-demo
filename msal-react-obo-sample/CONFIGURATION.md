# Configuration Guide

All configuration values for this project are centralized in configuration files for easy management and deployment.

## Configuration Files

### React App: `src/config.js`
Contains all React/frontend configuration including:
- Azure AD settings (client ID, tenant ID, authority)
- Python API endpoints
- Microsoft Graph configuration
- Azure AI Search settings (display only)
- Redirect URIs and cache settings

### Python API: `config.py`
Contains all Python/backend configuration including:
- Azure AD settings (client ID, secret, tenant ID)
- Microsoft Graph API settings
- Azure AI Search configuration (endpoint, index, API version)
- Server configuration (host, port, debug mode)
- CORS settings
- Query defaults (top, query type, fields)

## Quick Configuration

### 1. React App Configuration

Edit `demo/msal-react-obo-sample/msaljs-react-authflows-demo/src/config.js`:

```javascript
// Update Azure AD client ID and tenant
export const AZURE_AD_CONFIG = {
    clientId: "YOUR_REACT_CLIENT_ID",
    tenantId: "YOUR_TENANT_ID",
    authority: "https://login.microsoftonline.com/YOUR_TENANT_ID",
};

// Update Python API client ID
export const PYTHON_API_CONFIG = {
    clientId: "YOUR_API_CLIENT_ID",
    baseUrl: "http://localhost:5000",
    scope: "api://YOUR_API_CLIENT_ID/access_as_user"
};

// Update Azure AI Search (optional - for display only)
export const SEARCH_CONFIG = {
    endpoint: "https://YOUR_SEARCH_SERVICE.search.windows.net",
    index: "YOUR_INDEX_NAME",
    apiVersion: "2025-11-01-preview"
};
```

### 2. Python API Configuration

Edit `demo/msal-react-obo-sample/python-obo-api/config.py`:

```python
# Update Azure AD settings
AZURE_AD_CONFIG = {
    "client_id": "YOUR_API_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "tenant_id": "YOUR_TENANT_ID",
    "authority": "https://login.microsoftonline.com/YOUR_TENANT_ID"
}

# Update Azure AI Search settings
SEARCH_CONFIG = {
    "endpoint": "https://YOUR_SEARCH_SERVICE.search.windows.net",
    "index": "YOUR_INDEX_NAME",
    "api_version": "2025-11-01-preview",
    "scopes": ["https://search.azure.com/.default"],
    "api_key": os.environ.get("SEARCH_API_KEY", "YOUR_API_KEY"),
    "auth_mode": os.environ.get("SEARCH_AUTH_MODE", "OBO")
}
```

## Environment Variables

You can override Python configuration values using environment variables:

### Windows PowerShell:
```powershell
$env:SEARCH_AUTH_MODE="API_KEY"
$env:SEARCH_API_KEY="your-api-key-here"
```

### Linux/Mac:
```bash
export SEARCH_AUTH_MODE=API_KEY
export SEARCH_API_KEY=your-api-key-here
```

## Configuration Hierarchy

Python configuration values are resolved in this order:
1. Environment variables (highest priority)
2. Values in `config.py`
3. Default values in code (lowest priority)

## Security Best Practices

### ⚠️ Important Security Notes:

1. **Never commit secrets to Git**
   - Use environment variables for production
   - Use Azure Key Vault or similar for secrets management
   - The current `config.py` contains hardcoded secrets for demo purposes only

2. **For Production:**
   ```python
   # Use environment variables
   AZURE_AD_CONFIG = {
       "client_id": os.environ.get("AZURE_CLIENT_ID"),
       "client_secret": os.environ.get("AZURE_CLIENT_SECRET"),
       "tenant_id": os.environ.get("AZURE_TENANT_ID"),
       # ...
   }
   ```

3. **Add to `.gitignore`:**
   ```
   .env
   .env.local
   .env.production
   config.local.py
   ```

## Configuration Values Reference

### Azure AD
- **Client ID**: Application (client) ID from Azure Portal
- **Tenant ID**: Directory (tenant) ID from Azure Portal
- **Client Secret**: Secret value from Certificates & secrets
- **Authority**: `https://login.microsoftonline.com/{tenant_id}`

### Python API
- **Scope**: `api://{api_client_id}/access_as_user`
- **Base URL**: Where Python API runs (default: `http://localhost:5000`)

### Azure AI Search
- **Endpoint**: Your search service URL (e.g., `https://myservice.search.windows.net`)
- **Index**: Name of your search index
- **API Version**: `2025-11-01-preview` (required for query-time access control)
- **Auth Mode**: `OBO` (recommended) or `API_KEY` (fallback)

### Server Settings
- **Host**: `0.0.0.0` (accessible from network) or `127.0.0.1` (localhost only)
- **Port**: `5000` (default)
- **Debug**: `True` (development) or `False` (production)

## Query Customization

Modify search query defaults in `config.py`:

```python
QUERY_CONFIG = {
    "default_top": 50,              # Number of results to return
    "default_query_type": "simple", # Query parser type
    "default_orderby": "name asc",  # Default sort order
    "select_fields": "name,description,location,GroupIds,UserIds"  # Fields to return
}
```

## Troubleshooting

### Configuration Not Updating
1. Restart both React and Python servers after config changes
2. Clear browser cache and localStorage
3. Check for typos in config file imports

### Module Import Errors
```bash
# Make sure config.py is in the same directory as app.py
cd demo/msal-react-obo-sample/python-obo-api
ls config.py  # Should exist
```

### React Import Errors
```bash
# Make sure config.js is in src directory
cd demo/msal-react-obo-sample/msaljs-react-authflows-demo/src
ls config.js  # Should exist
```

## Migration Guide

If you have an existing setup with hardcoded values:

1. **Backup your current configuration values**
2. **Update config files** with your values
3. **Test locally** before deploying
4. **Update documentation** with your specific settings

## Additional Resources

- [Azure AD App Registration Guide](https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app)
- [Azure AI Search Setup](https://docs.microsoft.com/azure/search/search-create-service-portal)
- [Environment Variables in Flask](https://flask.palletsprojects.com/en/2.3.x/config/)
- [React Environment Variables](https://create-react-app.dev/docs/adding-custom-environment-variables/)
