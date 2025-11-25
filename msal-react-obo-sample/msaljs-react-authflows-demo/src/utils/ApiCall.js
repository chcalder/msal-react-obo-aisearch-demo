import { apiRequest, pythonApiConfig } from "../authConfig";
import { msalInstance } from "../index";

/**
 * Calls the Python OBO API with an access token
 * This demonstrates the On-Behalf-Of flow:
 * 1. Get token for Python API (not Microsoft Graph)
 * 2. Send token to Python API
 * 3. Python API uses OBO to get Graph token and call Microsoft Graph
 * 4. Python API returns result
 */
export async function callPythonOboApi(accessToken) {
    if (!accessToken) {
        const account = msalInstance.getActiveAccount();
        if (!account) {
            throw Error("No active account! Verify a user has been signed in and setActiveAccount has been called.");
        }
    
        // Acquire token with scope for the Python API (not Microsoft Graph!)
        const response = await msalInstance.acquireTokenSilent({
            ...apiRequest,  // Scope defined in config.js
            account: account
        });
        accessToken = response.accessToken;
        
        console.log("Access token acquired for Python API");
    }

    const headers = new Headers();
    const bearer = `Bearer ${accessToken}`;

    headers.append("Authorization", bearer);

    const options = {
        method: "GET",
        headers: headers
    };

    console.log(`Calling Python OBO API at: ${pythonApiConfig.endpoint}`);
    
    return fetch(pythonApiConfig.endpoint, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error("Error calling Python OBO API:", error);
            throw error;
        });
}
