"""
TickTick OAuth 2.0 flow - One-time setup to get access token.

TickTick API requires OAuth 2.0 for authentication.
This script guides you through the OAuth flow and saves your tokens.
"""

import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx
import json

# You need to register an app at https://developer.ticktick.com
# to get these credentials
CLIENT_ID = input("Enter your TickTick Client ID: ").strip()
CLIENT_SECRET = input("Enter your TickTick Client Secret: ").strip()

# OAuth endpoints
AUTH_URL = "https://ticktick.com/oauth/authorize"
TOKEN_URL = "https://ticktick.com/oauth/token"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "tasks:write tasks:read"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth callback."""

    auth_code = None

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>No authorization code received.</p>
                </body>
                </html>
            """)

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def main():
    """Run OAuth flow."""
    print("\n=== TickTick OAuth 2.0 Setup ===\n")

    # Step 1: Open browser for authorization
    auth_url = (
        f"{AUTH_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}&"
        f"response_type=code"
    )

    print("Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")
    webbrowser.open(auth_url)

    # Step 2: Start local server to receive callback
    print("Waiting for authorization callback...")
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.handle_request()

    if not OAuthCallbackHandler.auth_code:
        print("\n❌ Authorization failed - no code received")
        return

    print("✓ Authorization code received\n")

    # Step 3: Exchange code for access token
    print("Exchanging code for access token...")

    response = httpx.post(
        TOKEN_URL,
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': OAuthCallbackHandler.auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
        }
    )

    if response.status_code != 200:
        print(f"\n❌ Token exchange failed: {response.status_code}")
        print(response.text)
        return

    tokens = response.json()

    print("✓ Tokens received\n")
    print("=" * 60)
    print("Add these to your .env file:")
    print("=" * 60)
    print(f"\nTICKTICK_ACCESS_TOKEN={tokens['access_token']}")
    print(f"TICKTICK_CLIENT_ID={CLIENT_ID}")
    print(f"TICKTICK_CLIENT_SECRET={CLIENT_SECRET}\n")

    # Save to file for convenience
    with open('.ticktick_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)

    print("✓ Tokens saved to .ticktick_tokens.json")
    print("\nNext step: Run 'saturnus-setup' to get your project IDs\n")


if __name__ == "__main__":
    main()
