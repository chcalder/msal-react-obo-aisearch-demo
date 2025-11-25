import { useState } from "react";
import { AuthenticatedTemplate, UnauthenticatedTemplate, useMsal } from "@azure/msal-react";

import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Alert from "@mui/material/Alert";
import TextField from "@mui/material/TextField";

import { apiRequest } from "../authConfig";
import { callPythonOboApi } from "../utils/ApiCall";
import { API_ENDPOINTS, PYTHON_API_CONFIG } from "../config";

/**
 * Helper function to decode JWT access token
 * Extracts the payload (middle part) of the JWT and decodes it from base64
 * @param {string} token - The JWT token string
 * @returns {object|null} - Decoded token claims or null if parsing fails
 */
function parseJwt(token) {
  try {
    // Extract the payload part (between the two dots in JWT)
    const base64Url = token.split('.')[1];
    // Convert base64url to base64
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    // Decode base64 to JSON string
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    // Parse JSON string to object
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export function Home() {
  const { instance } = useMsal();
  
  // State to store decoded access token claims
  const [accessTokenClaims, setAccessTokenClaims] = useState(null);
  // State to track loading status during token acquisition
  const [loading, setLoading] = useState(false);
  
  // State for OBO API call
  const [oboLoading, setOboLoading] = useState(false);
  const [oboResponse, setOboResponse] = useState(null);
  const [oboError, setOboError] = useState(null);
  
  // State for AI Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchTokenClaims, setSearchTokenClaims] = useState(null);

  /**
   * Handler to request an access token for the Python OBO API
   * This token will be sent to Python API, which uses OBO to call Microsoft Graph
   * Uses MSAL's acquireTokenSilent to get token from cache or silently refresh
   */
  const handleRequestAccessToken = () => {
    const account = instance.getActiveAccount();
    if (account) {
      setLoading(true);
      
      // Request access token for Python API (NOT Microsoft Graph)
      // This is the Authorization Code Flow with PKCE
      // Scope defined in config.js: api://<client-id>/access_as_user
      instance.acquireTokenSilent({
        ...apiRequest, // Includes scope for Python OBO API
        account: account
      }).then(response => {
        // Decode the JWT access token to extract claims
        const claims = parseJwt(response.accessToken);
        setAccessTokenClaims(claims);
        setLoading(false);
        console.log("Access token acquired for Python OBO API");
      }).catch(error => {
        console.log("Error acquiring token:", error);
        setLoading(false);
      });
    }
  };

  /**
   * Handler to call Python OBO API
   * Demonstrates On-Behalf-Of flow:
   * 1. Get token for Python API (not Graph)
   * 2. Send token to Python API
   * 3. Python API uses OBO to get Graph token
   * 4. Python API calls Graph and returns result
   */
  const handleCallOboApi = async () => {
    setOboLoading(true);
    setOboError(null);
    setOboResponse(null);
    
    try {
      const response = await callPythonOboApi();
      console.log("OBO API Response:", response);
      setOboResponse(response);
      setOboLoading(false);
    } catch (error) {
      console.error("OBO API Error:", error);
      
      // Check if it's a consent error
      if (error.message && error.message.includes('AADSTS65001')) {
        setOboError('Consent required: Please grant admin consent in Azure Portal for the Python API permission, or log out and log back in to consent.');
      } else {
        setOboError(error.message);
      }
      setOboLoading(false);
    }
  };

  /**
   * Handler to search AI Search with OBO flow and security filtering
   */
  const handleAISearch = async () => {
    const account = instance.getActiveAccount();
    if (!account) {
      setSearchError("No active account. Please sign in.");
      return;
    }

    if (!searchQuery.trim()) {
      setSearchError("Please enter a search query");
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setSearchResults(null);

    try {
      // Acquire token for Python API
      const response = await instance.acquireTokenSilent({
        ...apiRequest,
        account: account
      });

      // Call Python API unified search endpoint (supports both OBO and API Key)
      const result = await fetch(API_ENDPOINTS.search, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${response.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery
        })
      });

      const data = await result.json();
      
      if (result.ok) {
        setSearchResults(data);
      } else {
        setSearchError(data.error || 'Failed to perform search');
      }
      
      setSearchLoading(false);
    } catch (error) {
      console.error('Error performing AI Search:', error);
      
      if (error.message && error.message.includes('AADSTS65001')) {
        setSearchError('Consent required: Please grant admin consent in Azure Portal for AI Search permission.');
      } else {
        setSearchError(error.message);
      }
      setSearchLoading(false);
    }
  };

  return (
      <Box sx={{ width: '100%', p: 2 }}>
          <AuthenticatedTemplate>
            {/* Action buttons */}
            <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {/* Button to trigger access token acquisition */}
              <Button variant="contained" color="primary" onClick={handleRequestAccessToken} disabled={loading}>
                {loading ? "Acquiring Token..." : "Request Access Token"}
              </Button>
              
              {/* Button to call Python OBO API */}
              <Button variant="contained" color="secondary" onClick={handleCallOboApi} disabled={oboLoading}>
                {oboLoading ? "Calling OBO API..." : "Call Python OBO API"}
              </Button>
            </Box>

            {/* AI Search with OBO or API Key */}
            <Box sx={{ mb: 3 }}>
              <Paper elevation={3} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                  Azure AI Search with Security Filtering
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Search with query-time access control based on your group membership. Supports both OBO flow and API key authentication.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <TextField
                    fullWidth
                    label="Search Query"
                    placeholder="Enter search terms (e.g., London)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !searchLoading) {
                        handleAISearch();
                      }
                    }}
                    variant="outlined"
                    size="small"
                  />
                  <Button 
                    variant="contained" 
                    color="success"
                    onClick={handleAISearch} 
                    disabled={searchLoading}
                    sx={{ minWidth: 120 }}
                  >
                    {searchLoading ? "Searching..." : "Search"}
                  </Button>
                </Box>
              </Paper>
            </Box>

            {/* Display AI Search Results */}
            {searchResults && (
              <Box sx={{ mb: 3 }}>
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="h6">{searchResults.message}</Typography>
                  <Typography variant="body2"><strong>Authentication:</strong> {searchResults.authentication}</Typography>
                  <Typography variant="body2">Found {searchResults.result_count} result(s)</Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Security Filter:</strong> {searchResults.security_filtering?.description}
                  </Typography>
                  {searchResults.search_token_info && (
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button 
                        variant="outlined" 
                        size="small"
                        onClick={() => setSearchTokenClaims({ 
                          incoming: searchResults.incoming_token_info,
                          search: searchResults.search_token_info 
                        })}
                      >
                        Compare Tokens (Incoming vs OBO)
                      </Button>
                    </Box>
                  )}
                </Alert>
                <Paper elevation={3} sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                    Search Results from Azure AI Search (margies-index)
                  </Typography>
                  <Box sx={{ mt: 2, maxHeight: '500px', overflow: 'auto' }}>
                    {searchResults.results && searchResults.results.length > 0 ? (
                      searchResults.results.map((result, index) => (
                        <Paper key={index} elevation={1} sx={{ p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
                          <Typography variant="h6" fontWeight="bold" color="primary">
                            {result.name || result.metadata_storage_name || result.id || `Result ${index + 1}`}
                          </Typography>
                          {result.location && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                              📍 {result.location}
                            </Typography>
                          )}
                          {result.description && (
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              {result.description}
                            </Typography>
                          )}
                          {result.content && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              {result.content.substring(0, 200)}...
                            </Typography>
                          )}
                          <Box sx={{ mt: 1, display: 'flex', gap: 2, alignItems: 'center' }}>
                            <Typography variant="caption" color="text.secondary">
                              Score: {result['@search.score']?.toFixed(2)}
                            </Typography>
                            {result.GroupIds && result.GroupIds.length > 0 && (
                              <Typography variant="caption" color="text.secondary">
                                Groups: {result.GroupIds.length}
                              </Typography>
                            )}
                            {result.UserIds && result.UserIds.length > 0 && (
                              <Typography variant="caption" color="text.secondary">
                                Users: {result.UserIds.length}
                              </Typography>
                            )}
                          </Box>
                        </Paper>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No results found matching your query and security permissions.
                      </Typography>
                    )}
                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
                      <Typography variant="subtitle2" gutterBottom>Full Response:</Typography>
                      <pre style={{ margin: 0, fontSize: '0.75rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '300px', overflow: 'auto' }}>
                        {JSON.stringify(searchResults, null, 2)}
                      </pre>
                    </Box>
                  </Box>
                </Paper>
              </Box>
            )}

            {/* Display AI Search Error */}
            {searchError && (
              <Box sx={{ mb: 3 }}>
                <Alert severity="error">
                  <Typography variant="body1"><strong>Error performing search:</strong></Typography>
                  <Typography variant="body2">{searchError}</Typography>
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    Make sure the Python API is running and has proper permissions for Azure AI Search
                  </Typography>
                </Alert>
              </Box>
            )}

            {/* Display OBO API Response */}
            {oboResponse && (
              <Box sx={{ mb: 3 }}>
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="h6">{oboResponse.message}</Typography>
                  <Typography variant="body2">{oboResponse.description}</Typography>
                </Alert>
                <Paper elevation={3} sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                    OBO API Response
                  </Typography>
                  <Box sx={{ mt: 2, maxHeight: '400px', overflow: 'auto' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(oboResponse, null, 2)}
                    </pre>
                  </Box>
                </Paper>
              </Box>
            )}

            {/* Display OBO API Error */}
            {oboError && (
              <Box sx={{ mb: 3 }}>
                <Alert severity="error">
                  <Typography variant="body1"><strong>Error calling OBO API:</strong></Typography>
                  <Typography variant="body2">{oboError}</Typography>
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    Make sure the Python API is running on {PYTHON_API_CONFIG.baseUrl}
                  </Typography>
                </Alert>
              </Box>
            )}

            {/* Responsive Grid Layout for Token Claims */}
            <Grid container spacing={3}>
              {/* ID Token Claims - obtained during login */}
              <Grid item xs={12} md={accessTokenClaims ? 6 : 12}>
                <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                  <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                    ID Token Claims
                  </Typography>
                  <Box sx={{ mt: 2, maxHeight: '600px', overflow: 'auto' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {instance.getActiveAccount() ? JSON.stringify(instance.getActiveAccount().idTokenClaims, null, 2) : null}
                    </pre>
                  </Box>
                </Paper>
              </Grid>

              {/* Display Access Token Claims - only shown after button click */}
              {/* This access token is for the Python OBO API (not Microsoft Graph) */}
              {/* The Python API will use OBO to exchange this for a Graph token */}
              {accessTokenClaims && (
                <Grid item xs={12} md={6}>
                  <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                    <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                      Access Token Claims (for Python OBO API)
                    </Typography>
                    <Box sx={{ mt: 2, maxHeight: '600px', overflow: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(accessTokenClaims, null, 2)}
                      </pre>
                    </Box>
                  </Paper>
                </Grid>
              )}

            </Grid>
          </AuthenticatedTemplate>

          <UnauthenticatedTemplate>
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography variant="h6">
                Please sign-in to see your profile information.
              </Typography>
            </Box>
          </UnauthenticatedTemplate>
      </Box>
  );
}