/**
 * Centralized Configuration for MSAL React Auth Flows Demo
 * 
 * All configuration values are defined here for easy management.
 * Update these values to match your Azure AD and API setup.
 */

// Azure AD Configuration
export const AZURE_AD_CONFIG = {
    clientId: "<YOUR_REACT_CLIENT_ID>",
    tenantId: "<YOUR_TENANT_ID>",
    authority: "https://login.microsoftonline.com/<YOUR_TENANT_ID>",
};

// Redirect URIs
export const REDIRECT_CONFIG = {
    redirectUri: "/",
    postLogoutRedirectUri: "/"
};

// Python API Configuration
export const PYTHON_API_CONFIG = {
    clientId: "<YOUR_API_CLIENT_ID>",
    baseUrl: "http://localhost:5000",
    scope: "api://<YOUR_API_CLIENT_ID>/access_as_user"
};

// API Endpoints
export const API_ENDPOINTS = {
    hello: `${PYTHON_API_CONFIG.baseUrl}/api/hello`,
    search: `${PYTHON_API_CONFIG.baseUrl}/api/search-unified`,
    searchSimple: `${PYTHON_API_CONFIG.baseUrl}/api/search-simple`,
    oboSearch: `${PYTHON_API_CONFIG.baseUrl}/api/search`
};

// Microsoft Graph Configuration
export const GRAPH_CONFIG = {
    endpoint: "https://graph.microsoft.com/v1.0/me",
    scopes: ["User.Read"]
};

// Cache Configuration
export const CACHE_CONFIG = {
    cacheLocation: "localStorage",
    storeAuthStateInCookie: false // Set to true if supporting IE/Edge/Firefox
};

// Azure AI Search Configuration (for display/documentation purposes)
export const SEARCH_CONFIG = {
    endpoint: "https://<YOUR_SEARCH_SERVICE>.search.windows.net",
    index: "<YOUR_INDEX_NAME>",
    apiVersion: "2025-11-01-preview"
};
