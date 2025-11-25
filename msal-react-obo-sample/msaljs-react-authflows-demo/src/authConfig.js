import { LogLevel } from "@azure/msal-browser";
import { AZURE_AD_CONFIG, REDIRECT_CONFIG, CACHE_CONFIG } from "./config";

// Browser check variables
// If you support IE, our recommendation is that you sign-in using Redirect APIs
// If you as a developer are testing using Edge InPrivate mode, please add "isEdge" to the if check
const ua = window.navigator.userAgent;
const msie = ua.indexOf("MSIE ");
const msie11 = ua.indexOf("Trident/");
const msedge = ua.indexOf("Edge/");
const firefox = ua.indexOf("Firefox");
const isIE = msie > 0 || msie11 > 0;
const isEdge = msedge > 0;
const isFirefox = firefox > 0; // Only needed if you need to support the redirect flow in Firefox incognito

/**
 * Configuration object to be passed to MSAL instance on creation. 
 * For a full list of MSAL.js configuration parameters, visit:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md 
 */
export const msalConfig = {
    auth: {
        clientId: AZURE_AD_CONFIG.clientId,
        authority: AZURE_AD_CONFIG.authority,
        redirectUri: REDIRECT_CONFIG.redirectUri,
        postLogoutRedirectUri: REDIRECT_CONFIG.postLogoutRedirectUri
    },
    cache: {
        cacheLocation: CACHE_CONFIG.cacheLocation,
        storeAuthStateInCookie: CACHE_CONFIG.storeAuthStateInCookie || isIE || isEdge || isFirefox
    },
    system: {
        allowPlatformBroker: false, // Disables WAM Broker
        loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        console.error(message);
                        return;
                    case LogLevel.Info:
                        console.info(message);
                        return;
                    case LogLevel.Verbose:
                        console.debug(message);
                        return;
                    case LogLevel.Warning:
                        console.warn(message);
                        return;
                    default:
                        return;
                }
            }
        }
    }
};

import { GRAPH_CONFIG, PYTHON_API_CONFIG, API_ENDPOINTS } from "./config";

/**
 * Scopes you add here will be prompted for user consent during sign-in.
 * By default, MSAL.js will add OIDC scopes (openid, profile, email) to any login request.
 * For more information about OIDC scopes, visit: 
 * https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent#openid-connect-scopes
 */
export const loginRequest = {
    scopes: GRAPH_CONFIG.scopes
};

/**
 * Add here the scopes to request when obtaining an access token for MS Graph API. For more information, see:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/resources-and-scopes.md
 */
export const graphConfig = {
    graphMeEndpoint: GRAPH_CONFIG.endpoint
};

/**
 * Scopes for calling the Python OBO API
 * This token will be sent to the Python API, which will then use OBO to call Microsoft Graph
 */
export const apiRequest = {
    scopes: [PYTHON_API_CONFIG.scope]
};

/**
 * Configuration for the Python OBO API endpoint
 */
export const pythonApiConfig = {
    endpoint: API_ENDPOINTS.hello
};
