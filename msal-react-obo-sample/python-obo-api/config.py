"""
Centralized Configuration for Python OBO API

All configuration values are defined here for easy management.
Update these values to match your Azure AD and service setup.
"""

import os

# ============================================================================
# Azure AD Configuration
# ============================================================================
AZURE_AD_CONFIG = {
    "client_id": "<YOUR_API_CLIENT_ID>",
    "client_secret": "<YOUR_CLIENT_SECRET>",
    "tenant_id": "<YOUR_TENANT_ID>",
    "authority": "https://login.microsoftonline.com/<YOUR_TENANT_ID>"
}

# ============================================================================
# Microsoft Graph Configuration
# ============================================================================
GRAPH_CONFIG = {
    "scopes": ["https://graph.microsoft.com/User.Read"],
    "member_of_endpoint": "https://graph.microsoft.com/v1.0/me/memberOf"
}

# ============================================================================
# Azure AI Search Configuration
# ============================================================================
SEARCH_CONFIG = {
    "endpoint": "https://<YOUR_SEARCH_SERVICE>.search.windows.net",
    "index": "<YOUR_INDEX_NAME>",
    "api_version": "2025-11-01-preview",
    "scopes": ["https://search.azure.com/.default"],
    "api_key": os.environ.get("SEARCH_API_KEY", "<YOUR_SEARCH_API_KEY>"),
    "auth_mode": os.environ.get("SEARCH_AUTH_MODE", "OBO")  # "OBO" or "API_KEY"
}

# ============================================================================
# API Server Configuration
# ============================================================================
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True
}

# ============================================================================
# CORS Configuration
# ============================================================================
CORS_CONFIG = {
    "origins": ["http://localhost:3000"],
    "supports_credentials": True
}

# ============================================================================
# Search Query Configuration
# ============================================================================
QUERY_CONFIG = {
    "default_top": 50,
    "default_query_type": "simple",
    "default_orderby": "name asc",
    "select_fields": "name,description,location,GroupIds,UserIds"
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_authority():
    """Get the Azure AD authority URL"""
    return AZURE_AD_CONFIG["authority"]

def get_client_id():
    """Get the Azure AD client ID"""
    return AZURE_AD_CONFIG["client_id"]

def get_client_secret():
    """Get the Azure AD client secret"""
    return AZURE_AD_CONFIG["client_secret"]

def get_tenant_id():
    """Get the Azure AD tenant ID"""
    return AZURE_AD_CONFIG["tenant_id"]

def get_graph_scopes():
    """Get Microsoft Graph API scopes"""
    return GRAPH_CONFIG["scopes"]

def get_search_scopes():
    """Get Azure AI Search scopes"""
    return SEARCH_CONFIG["scopes"]

def get_search_endpoint():
    """Get Azure AI Search endpoint"""
    return SEARCH_CONFIG["endpoint"]

def get_search_index():
    """Get Azure AI Search index name"""
    return SEARCH_CONFIG["index"]

def get_search_api_version():
    """Get Azure AI Search API version"""
    return SEARCH_CONFIG["api_version"]

def get_search_auth_mode():
    """Get Azure AI Search authentication mode"""
    return SEARCH_CONFIG["auth_mode"]

def get_search_api_key():
    """Get Azure AI Search API key"""
    return SEARCH_CONFIG["api_key"]
