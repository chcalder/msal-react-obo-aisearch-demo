"""
Python Flask API demonstrating On-Behalf-Of (OBO) flow
This API receives a token from the React SPA and uses OBO to call Microsoft Graph
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import msal
import requests
import jwt
import os

# Import centralized configuration
from config import (
    AZURE_AD_CONFIG, GRAPH_CONFIG, SEARCH_CONFIG, SERVER_CONFIG,
    get_authority, get_client_id, get_client_secret,
    get_graph_scopes, get_search_scopes, get_search_endpoint,
    get_search_index, get_search_api_version, get_search_auth_mode,
    get_search_api_key, QUERY_CONFIG
)

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Configuration shortcuts for backward compatibility
CLIENT_ID = get_client_id()
CLIENT_SECRET = get_client_secret()
TENANT_ID = AZURE_AD_CONFIG["tenant_id"]
AUTHORITY = get_authority()
SCOPE = get_graph_scopes()

# Azure AI Search Configuration
SEARCH_ENDPOINT = get_search_endpoint()
SEARCH_INDEX = get_search_index()
SEARCH_SCOPE = get_search_scopes()
SEARCH_API_KEY = get_search_api_key()
SEARCH_AUTH_MODE = get_search_auth_mode()

@app.route('/api/hello', methods=['GET'])
def hello():
    """
    Endpoint that demonstrates OBO flow
    1. Receives access token from React SPA
    2. Uses OBO to get a new token for Microsoft Graph
    3. Calls Microsoft Graph API
    4. Returns combined result
    """
    
    # Step 1: Extract the access token from Authorization header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "error": "Missing or invalid Authorization header"
        }), 401
    
    # Get the token (remove "Bearer " prefix)
    user_access_token = auth_header.split(' ')[1]
    
    try:
        # Step 2: Use the OBO flow to get a token for Microsoft Graph
        # Create a confidential client application
        msal_app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            client_credential=CLIENT_SECRET
        )
        
        # Perform OBO token exchange
        result = msal_app.acquire_token_on_behalf_of(
            user_assertion=user_access_token,
            scopes=SCOPE
        )
        
        if "access_token" not in result:
            error_description = result.get("error_description", "Unknown error")
            return jsonify({
                "error": "OBO token acquisition failed",
                "details": error_description
            }), 500
        
        graph_access_token = result['access_token']
        
        # Decode both tokens to compare them
        incoming_token_decoded = jwt.decode(user_access_token, options={"verify_signature": False})
        obo_token_decoded = jwt.decode(graph_access_token, options={"verify_signature": False})
        
        # Step 3: Call Microsoft Graph with the new token
        graph_endpoint = "https://graph.microsoft.com/v1.0/me"
        headers = {
            'Authorization': f'Bearer {graph_access_token}'
        }
        
        graph_response = requests.get(graph_endpoint, headers=headers)
        
        if graph_response.status_code != 200:
            return jsonify({
                "error": "Failed to call Microsoft Graph",
                "status": graph_response.status_code
            }), 500
        
        user_data = graph_response.json()
        
        # Step 3b: Query user's groups using the OBO token with GroupMember.Read.All permission
        groups_endpoint = "https://graph.microsoft.com/v1.0/me/memberOf"
        groups_response = requests.get(groups_endpoint, headers=headers)
        obo_queried_groups = []
        if groups_response.status_code == 200:
            groups_data = groups_response.json()
            obo_queried_groups = [group.get('id') for group in groups_data.get('value', []) if group.get('@odata.type') == '#microsoft.graph.group']
        
        # Step 4: Extract claims from both tokens
        incoming_groups = incoming_token_decoded.get("groups", [])
        incoming_roles = incoming_token_decoded.get("roles", [])
        obo_groups = obo_token_decoded.get("groups", [])
        obo_roles = obo_token_decoded.get("roles", [])
        
        # Step 5: Return combined result with token information
        return jsonify({
            "message": "Hello World from Python OBO API!",
            "flow": "On-Behalf-Of (OBO) Flow Successful",
            "user_info": {
                "displayName": user_data.get("displayName"),
                "userPrincipalName": user_data.get("userPrincipalName"),
                "jobTitle": user_data.get("jobTitle"),
                "id": user_data.get("id")
            },
            "incoming_token_info": {
                "aud": incoming_token_decoded.get("aud"),
                "iss": incoming_token_decoded.get("iss"),
                "scp": incoming_token_decoded.get("scp"),
                "appid": incoming_token_decoded.get("appid"),
                "groups": incoming_groups,
                "roles": incoming_roles,
                "group_count": len(incoming_groups),
                "token_type": "Access token for Python API"
            },
            "obo_token_info": {
                "aud": obo_token_decoded.get("aud"),
                "iss": obo_token_decoded.get("iss"),
                "scp": obo_token_decoded.get("scp"),
                "appid": obo_token_decoded.get("appid"),
                "groups_in_token": obo_groups,
                "groups_in_token_count": len(obo_groups),
                "groups_queried_via_api": obo_queried_groups,
                "groups_queried_count": len(obo_queried_groups),
                "roles": obo_roles,
                "token_type": "OBO Access token for Microsoft Graph",
                "obtained_via": "On-Behalf-Of flow",
                "note": "Graph tokens don't include group claims. Groups must be queried via /me/memberOf API."
            },
            "token_comparison": {
                "same_user": incoming_token_decoded.get("oid") == obo_token_decoded.get("oid"),
                "different_audience": incoming_token_decoded.get("aud") != obo_token_decoded.get("aud"),
                "incoming_audience": incoming_token_decoded.get("aud"),
                "obo_audience": obo_token_decoded.get("aud")
            },
            "description": "This shows both the incoming token (from React) and the OBO token (for Graph)"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Exception occurred",
            "details": str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_with_obo():
    """
    Endpoint that demonstrates OBO flow with Azure AI Search
    1. Receives access token from React SPA
    2. Uses OBO to get a new token for Azure AI Search
    3. Extracts user's groups for security filtering
    4. Calls Azure AI Search with security filter
    5. Returns filtered search results
    """
    try:
        # Step 1: Extract the incoming access token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No authorization token provided"}), 401
        
        user_access_token = auth_header.split(' ')[1]
        
        # Step 2: Use OBO to get token for AI Search
        msal_app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            client_credential=CLIENT_SECRET
        )
        
        result = msal_app.acquire_token_on_behalf_of(
            user_assertion=user_access_token,
            scopes=SEARCH_SCOPE
        )
        
        if "error" in result:
            error_description = result.get("error_description", "Unknown error")
            error_code = result.get("error")
            print(f"OBO Error for AI Search: {error_code}")
            print(f"Error Description: {error_description}")
            print(f"Scopes requested: {SEARCH_SCOPE}")
            return jsonify({
                "error": "OBO token acquisition failed for AI Search",
                "details": error_description,
                "error_code": error_code,
                "scopes_requested": SEARCH_SCOPE,
                "suggestion": "Check if Azure AD permission 'https://search.azure.com/user_impersonation' is granted and consented"
            }), 500
        
        search_access_token = result['access_token']
        
        # Step 3: Extract user's groups from original token for filtering
        token_decoded = jwt.decode(user_access_token, options={"verify_signature": False})
        user_groups = token_decoded.get("groups", [])
        user_oid = token_decoded.get("oid")
        user_upn = token_decoded.get("upn")
        
        # Step 4: Get search query from request
        request_data = request.get_json()
        search_query = request_data.get("query", "*")
        
        # Step 5: Build security filter based on user's groups
        if user_groups:
            group_filters = " or ".join([f"g eq '{group}'" for group in user_groups])
            security_filter = f"security_groups/any(g: {group_filters})"
            filter_description = f"User can see documents where security_groups contains one of their {len(user_groups)} group(s)"
        else:
            # If user has no groups, don't apply a filter (show all results)
            security_filter = None
            filter_description = "User has no groups, showing all documents (no security filter)"
        
        # Step 6: Call AI Search with OBO token
        search_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version={get_search_api_version()}"
        
        headers = {
            "Authorization": f"Bearer {search_access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "search": search_query,
            "select": "*",
            "top": QUERY_CONFIG["default_top"],
            "queryType": QUERY_CONFIG["default_query_type"]
        }
        
        # Only add filter if user has groups
        if security_filter:
            payload["filter"] = security_filter
        
        # Step 7: Make the request
        search_response = requests.post(search_url, headers=headers, json=payload)
        
        if search_response.status_code != 200:
            return jsonify({
                "error": "AI Search request failed",
                "status": search_response.status_code,
                "details": search_response.text
            }), search_response.status_code
        
        search_results = search_response.json()
        
        # Step 8: Return combined results
        return jsonify({
            "message": "AI Search completed successfully using OBO flow",
            "flow": "React SPA -> Python API (OBO) -> Azure AI Search",
            "user_context": {
                "oid": user_oid,
                "upn": user_upn,
                "groups": user_groups,
                "group_count": len(user_groups)
            },
            "security_filtering": {
                "filter": security_filter,
                "description": filter_description
            },
            "search_query": search_query,
            "result_count": search_results.get("@odata.count", len(search_results.get("value", []))),
            "results": search_results.get("value", [])
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Exception occurred",
            "details": str(e)
        }), 500

@app.route('/api/search-simple', methods=['POST'])
def search_simple():
    """
    Simpler search endpoint using API key instead of OBO
    Still demonstrates security filtering based on user groups
    """
    try:
        print(f"Search endpoint called")
        print(f"SEARCH_API_KEY configured: {bool(SEARCH_API_KEY)}")
        
        if not SEARCH_API_KEY:
            return jsonify({
                "error": "SEARCH_API_KEY not configured",
                "instruction": "Set SEARCH_API_KEY environment variable with your AI Search admin or query key"
            }), 500
        
        # Extract user's groups from token for security filtering
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No authorization token provided"}), 401
        
        user_access_token = auth_header.split(' ')[1]
        token_decoded = jwt.decode(user_access_token, options={"verify_signature": False})
        user_groups = token_decoded.get("groups", [])
        user_oid = token_decoded.get("oid")
        user_upn = token_decoded.get("upn")
        
        print(f"User: {user_upn}, Groups: {len(user_groups)}")
        
        # Get search query
        request_data = request.get_json()
        search_query = request_data.get("query", "*")
        
        # Build security filter
        if user_groups:
            group_filters = " or ".join([f"g eq '{group}'" for group in user_groups])
            security_filter = f"security_groups/any(g: {group_filters})"
            filter_description = f"User can see documents where security_groups contains one of their {len(user_groups)} group(s)"
        else:
            # If user has no groups, don't apply a filter (show all results)
            # In production, you might want to restrict this differently
            security_filter = None
            filter_description = "User has no groups, showing all documents (no security filter)"
        
        # Call AI Search with API key (no OBO)
        search_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version={get_search_api_version()}"
        
        headers = {
            "api-key": SEARCH_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "search": search_query,
            "select": "*",
            "top": QUERY_CONFIG["default_top"],
            "queryType": QUERY_CONFIG["default_query_type"]
        }
        
        # Only add filter if user has groups
        if security_filter:
            payload["filter"] = security_filter
        
        print(f"Calling AI Search: {search_url}")
        print(f"Security filter: {security_filter}")
        
        search_response = requests.post(search_url, headers=headers, json=payload)
        
        print(f"AI Search response status: {search_response.status_code}")
        
        if search_response.status_code != 200:
            print(f"AI Search error: {search_response.text}")
            return jsonify({
                "error": "AI Search request failed",
                "status": search_response.status_code,
                "details": search_response.text
            }), search_response.status_code
        
        search_results = search_response.json()
        
        return jsonify({
            "message": "AI Search completed successfully (using API key)",
            "flow": "React SPA -> Python API -> Azure AI Search (with API key)",
            "user_context": {
                "oid": user_oid,
                "upn": user_upn,
                "groups": user_groups,
                "group_count": len(user_groups)
            },
            "security_filtering": {
                "filter": security_filter,
                "description": filter_description
            },
            "search_query": search_query,
            "result_count": search_results.get("@odata.count", len(search_results.get("value", []))),
            "results": search_results.get("value", [])
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Exception occurred",
            "details": str(e)
        }), 500

@app.route('/api/search-unified', methods=['POST'])
def search_unified():
    """
    Unified search endpoint that supports both OBO and API Key authentication
    Controlled by SEARCH_AUTH_MODE environment variable
    """
    try:
        print(f"Unified search endpoint called with mode: {SEARCH_AUTH_MODE}")
        
        # Extract user's access token and groups
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No authorization token provided"}), 401
        
        user_access_token = auth_header.split(' ')[1]
        
        # Decode the INCOMING token from React (contains user's groups)
        # NOTE: Groups come from THIS token, not from the Azure Search OBO token
        # The Azure Search OBO token is scoped for search and won't contain group claims
        token_decoded = jwt.decode(user_access_token, options={"verify_signature": False})
        user_groups = token_decoded.get("groups", [])
        user_oid = token_decoded.get("oid")
        user_upn = token_decoded.get("upn")
        
        # Get search query
        request_data = request.get_json()
        search_query = request_data.get("query", "*")
        
        print(f"User: {user_upn} (OID: {user_oid}), Groups from incoming token: {len(user_groups)}, Query: {search_query}")
        
        # Using query-time access control - Azure AI Search handles filtering based on token
        # No manual filter construction needed
        filter_description = "Query-time access control: Azure AI Search evaluates GroupIds/UserIds based on user's token"
        
        # Choose authentication method
        if SEARCH_AUTH_MODE == "OBO":
            # Use OBO flow
            print("Using OBO authentication for AI Search")
            msal_app = msal.ConfidentialClientApplication(
                CLIENT_ID,
                authority=AUTHORITY,
                client_credential=CLIENT_SECRET
            )
            
            result = msal_app.acquire_token_on_behalf_of(
                user_assertion=user_access_token,
                scopes=SEARCH_SCOPE
            )
            
            if "error" in result:
                error_description = result.get("error_description", "Unknown error")
                error_code = result.get("error")
                correlation_id = result.get("correlation_id", "N/A")
                print(f"OBO Error for AI Search: {error_code}")
                print(f"Error Description: {error_description}")
                print(f"Correlation ID: {correlation_id}")
                print(f"Scopes requested: {SEARCH_SCOPE}")
                return jsonify({
                    "error": "OBO token acquisition failed for AI Search",
                    "details": error_description,
                    "error_code": error_code,
                    "correlation_id": correlation_id,
                    "scopes_requested": SEARCH_SCOPE,
                    "suggestion": "The 'invalid_grant' error often means the Azure AD permission isn't configured or consented. Try setting SEARCH_AUTH_MODE=API_KEY as a workaround."
                }), 500
            
            search_access_token = result['access_token']
            # Decode the OBO token for inspection
            search_token_decoded = jwt.decode(search_access_token, options={"verify_signature": False})
            headers = {
                "Authorization": f"Bearer {search_access_token}",
                "x-ms-query-source-authorization": search_access_token,
                "Content-Type": "application/json"
            }
            auth_method = "OBO Flow with Query-Time Access Control"
        else:
            # Use API Key
            print("Using API Key authentication for AI Search")
            if not SEARCH_API_KEY:
                return jsonify({
                    "error": "SEARCH_API_KEY not configured",
                    "instruction": "Set SEARCH_API_KEY environment variable or use SEARCH_AUTH_MODE=OBO"
                }), 500
            
            headers = {
                "api-key": SEARCH_API_KEY,
                "Content-Type": "application/json"
            }
            auth_method = "API Key"
        
        # Call AI Search with query-time access control
        search_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version={get_search_api_version()}"
        
        payload = {
            "search": search_query,
            "select": QUERY_CONFIG["select_fields"],
            "top": QUERY_CONFIG["default_top"],
            "queryType": QUERY_CONFIG["default_query_type"],
            "orderby": QUERY_CONFIG["default_orderby"]
        }
        # No manual filter needed - Azure AI Search handles access control based on x-ms-query-source-authorization header
        
        print(f"Calling AI Search with {auth_method}")
        print(f"Access control: {filter_description}")
        print(f"Search URL: {search_url}")
        
        search_response = requests.post(search_url, headers=headers, json=payload)
        
        print(f"AI Search response status: {search_response.status_code}")
        
        if search_response.status_code != 200:
            error_detail = search_response.text
            print(f"AI Search error ({search_response.status_code}): {error_detail}")
            
            # Add specific guidance for 403 errors
            if search_response.status_code == 403:
                suggestion = "403 Forbidden: The OBO token doesn't have permission to access the search index. " \
                            "Ensure the user (or service principal) has 'Search Index Data Reader' role assigned on the Azure AI Search service. " \
                            "For user-based OBO, the signed-in user needs the role, not just the service principal."
            else:
                suggestion = f"HTTP {search_response.status_code} error from Azure AI Search"
            
            return jsonify({
                "error": "AI Search request failed",
                "status": search_response.status_code,
                "details": error_detail,
                "auth_method": auth_method,
                "suggestion": suggestion
            }), search_response.status_code
        
        search_results = search_response.json()
        
        response_data = {
            "message": "AI Search completed successfully",
            "authentication": auth_method,
            "flow": f"React SPA -> Python API ({auth_method}) -> Azure AI Search",
            "user_context": {
                "oid": user_oid,
                "upn": user_upn,
                "groups": user_groups,
                "group_count": len(user_groups),
                "groups_source": "Incoming token from React (not from OBO token)"
            },
            "security_filtering": {
                "method": "query-time access control",
                "description": filter_description,
                "note": "Azure AI Search evaluates access based on x-ms-query-source-authorization header"
            },
            "search_query": search_query,
            "result_count": search_results.get("@odata.count", len(search_results.get("value", []))),
            "results": search_results.get("value", [])
        }
        
        # Add token information if OBO was used
        if SEARCH_AUTH_MODE == "OBO" and 'search_token_decoded' in locals():
            response_data["incoming_token_info"] = {
                "aud": token_decoded.get("aud"),
                "iss": token_decoded.get("iss"),
                "oid": token_decoded.get("oid"),
                "upn": token_decoded.get("upn"),
                "appid": token_decoded.get("appid"),
                "scp": token_decoded.get("scp"),
                "groups": user_groups,
                "group_count": len(user_groups),
                "token_type": "Incoming Access Token from React (contains groups)"
            }
            response_data["search_token_info"] = {
                "aud": search_token_decoded.get("aud"),
                "iss": search_token_decoded.get("iss"),
                "oid": search_token_decoded.get("oid"),
                "upn": search_token_decoded.get("upn"),
                "appid": search_token_decoded.get("appid"),
                "scp": search_token_decoded.get("scp"),
                "roles": search_token_decoded.get("roles", []),
                "groups": search_token_decoded.get("groups", []),
                "exp": search_token_decoded.get("exp"),
                "token_type": "OBO Access Token for Azure AI Search (scoped for search, no groups)"
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Exception in search_unified: {str(e)}")
        return jsonify({
            "error": "Exception occurred",
            "details": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Python OBO API is running"}), 200

if __name__ == '__main__':
    print(f"Starting Python OBO API on http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print("OBO Flow: React SPA -> Python API -> Microsoft Graph")
    print(f"AI Search: React SPA -> Python API ({SEARCH_AUTH_MODE}) -> Azure AI Search")
    app.run(debug=SERVER_CONFIG['debug'], host=SERVER_CONFIG['host'], port=SERVER_CONFIG['port'])
