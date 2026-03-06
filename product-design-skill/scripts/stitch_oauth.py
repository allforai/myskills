#!/usr/bin/env python3
"""
Stitch MCP OAuth helper.

Replaces `npx -y @_davideast/stitch-mcp init` with a lightweight Python
script that doesn't need interactive terminal selection or bundled gcloud.

Modes:
  --browser       (default) Start local HTTP server, open browser, receive callback automatically.
  --manual        Print URL, user pastes verification code back. Works in any environment.
  --generate-url  Step 1 of non-interactive flow: print auth URL, save PKCE params to temp file.
  --exchange CODE  Step 2 of non-interactive flow: exchange verification code using saved PKCE params.

Usage:
  python3 stitch_oauth.py              # auto mode (tries browser, falls back to manual)
  python3 stitch_oauth.py --browser    # force browser callback mode
  python3 stitch_oauth.py --manual     # force manual paste mode
  python3 stitch_oauth.py --check      # just check if credentials exist
  python3 stitch_oauth.py --generate-url  # print URL, save PKCE (for automation)
  python3 stitch_oauth.py --exchange CODE # exchange code using saved PKCE (for automation)
"""

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request

# Google Cloud SDK default OAuth client (public, same as gcloud CLI uses)
CLIENT_ID = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"
CLIENT_SECRET = "d-FL95Q19q7MQmFpd7hHD0Ty"
SCOPES = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/sqlservice.login"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

STITCH_CONFIG_DIR = os.path.expanduser("~/.stitch-mcp/config")
ADC_PATH = os.path.join(STITCH_CONFIG_DIR, "application_default_credentials.json")
PKCE_TEMP_PATH = "/tmp/stitch-oauth-pkce.json"

# PKCE
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
state = secrets.token_urlsafe(32)


def check_credentials():
    """Check if valid credentials exist."""
    if os.path.exists(ADC_PATH):
        try:
            with open(ADC_PATH) as f:
                data = json.load(f)
            if data.get("refresh_token"):
                print(f"OK: credentials exist at {ADC_PATH}")
                return True
        except (json.JSONDecodeError, KeyError):
            pass
    print(f"MISSING: no valid credentials at {ADC_PATH}")
    return False


def exchange_code(code, redirect_uri, verifier=None):
    """Exchange authorization code for tokens."""
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier or code_verifier,
    }).encode()
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def save_credentials(token_data):
    """Save as application_default_credentials.json."""
    if "refresh_token" not in token_data:
        print(f"ERROR: no refresh_token in response:\n{json.dumps(token_data, indent=2)}")
        sys.exit(1)
    os.makedirs(STITCH_CONFIG_DIR, exist_ok=True)
    adc = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_data["refresh_token"],
        "type": "authorized_user",
    }
    with open(ADC_PATH, "w") as f:
        json.dump(adc, f, indent=2)
    os.chmod(ADC_PATH, 0o600)
    print(f"Credentials saved to: {ADC_PATH}")


def build_auth_url(redirect_uri):
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    return f"https://accounts.google.com/o/oauth2/auth?{params}"


def mode_browser():
    """Browser callback mode: start local server, open browser."""
    import webbrowser

    port = 8085
    redirect_uri = f"http://localhost:{port}"
    auth_url = build_auth_url(redirect_uri)
    auth_code = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in params and params.get("state", [None])[0] == state:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("localhost", port), Handler)
    server.timeout = 120
    print(f"Opening browser for Google OAuth...")
    print(f"If browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)
    print("Waiting for authorization (timeout: 120s)...")
    while auth_code is None:
        server.handle_request()
    server.server_close()

    print("Exchanging code for tokens...")
    token_data = exchange_code(auth_code, redirect_uri)
    save_credentials(token_data)


def mode_manual():
    """Manual mode: start localhost server, print URL, wait for callback."""
    port = 8085
    redirect_uri = f"http://localhost:{port}"
    auth_url = build_auth_url(redirect_uri)
    auth_code = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in params and params.get("state", [None])[0] == state:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("localhost", port), Handler)
    server.timeout = 120
    print(f"\nOpen this URL in any browser:\n\n{auth_url}\n")
    print(f"Listening on http://localhost:{port} for callback (timeout: 120s)...")
    while auth_code is None:
        server.handle_request()
    server.server_close()

    print("Exchanging code for tokens...")
    token_data = exchange_code(auth_code, redirect_uri)
    save_credentials(token_data)


def mode_generate_url():
    """Non-interactive step 1: print auth URL, save PKCE params to temp file.
    Uses localhost redirect — run --listen after opening the URL in browser."""
    port = 8085
    redirect_uri = f"http://localhost:{port}"
    auth_url = build_auth_url(redirect_uri)

    pkce_data = {
        "verifier": code_verifier,
        "state": state,
        "redirect_uri": redirect_uri,
        "port": port,
    }
    with open(PKCE_TEMP_PATH, "w") as f:
        json.dump(pkce_data, f)

    print(f"AUTH_URL={auth_url}")
    print(f"\nPKCE params saved to {PKCE_TEMP_PATH}")
    print("Next: open the URL in browser, then run: python3 stitch_oauth.py --listen")


def mode_listen():
    """Non-interactive step 2: start localhost server, wait for OAuth callback."""
    if not os.path.exists(PKCE_TEMP_PATH):
        print(f"ERROR: PKCE params not found at {PKCE_TEMP_PATH}")
        print("Run --generate-url first.")
        sys.exit(1)

    with open(PKCE_TEMP_PATH) as f:
        pkce_data = json.load(f)

    port = pkce_data["port"]
    saved_state = pkce_data["state"]
    auth_code = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in params and params.get("state", [None])[0] == saved_state:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("localhost", port), Handler)
    server.timeout = 120
    print(f"Listening on http://localhost:{port} for OAuth callback (timeout: 120s)...")
    while auth_code is None:
        server.handle_request()
    server.server_close()

    print("Exchanging code for tokens...")
    token_data = exchange_code(auth_code, pkce_data["redirect_uri"], pkce_data["verifier"])
    save_credentials(token_data)

    os.remove(PKCE_TEMP_PATH)
    print("PKCE temp file cleaned up.")


def mode_exchange(code):
    """Non-interactive step 3 (alternative): exchange code directly using saved PKCE params."""
    if not os.path.exists(PKCE_TEMP_PATH):
        print(f"ERROR: PKCE params not found at {PKCE_TEMP_PATH}")
        print("Run --generate-url first.")
        sys.exit(1)

    with open(PKCE_TEMP_PATH) as f:
        pkce_data = json.load(f)

    print("Exchanging code for tokens...")
    token_data = exchange_code(code, pkce_data["redirect_uri"], pkce_data["verifier"])
    save_credentials(token_data)

    os.remove(PKCE_TEMP_PATH)
    print("PKCE temp file cleaned up.")


def main():
    parser = argparse.ArgumentParser(description="Stitch MCP OAuth helper")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--browser", action="store_true", help="Browser callback mode (default)")
    group.add_argument("--manual", action="store_true", help="Manual paste mode")
    group.add_argument("--check", action="store_true", help="Check if credentials exist")
    group.add_argument("--generate-url", action="store_true", help="Print auth URL, save PKCE (step 1)")
    group.add_argument("--listen", action="store_true", help="Start localhost server for callback (step 2)")
    group.add_argument("--exchange", metavar="CODE", help="Exchange code directly (step 2 alt)")
    args = parser.parse_args()

    if args.check:
        sys.exit(0 if check_credentials() else 1)

    if args.generate_url:
        mode_generate_url()
        return

    if args.listen:
        mode_listen()
        print("\nDone! Now register MCP (if not already):")
        print("  claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy")
        print("Then restart Claude Code.")
        return

    if args.exchange:
        mode_exchange(args.exchange)
        print("\nDone! Now register MCP (if not already):")
        print("  claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy")
        print("Then restart Claude Code.")
        return

    if args.manual:
        mode_manual()
    elif args.browser:
        mode_browser()
    else:
        # Auto: try browser, fall back to manual on error
        try:
            mode_browser()
        except (OSError, KeyboardInterrupt):
            print("\nBrowser mode failed, falling back to manual mode...\n")
            mode_manual()

    print("\nDone! Now register MCP (if not already):")
    print("  claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy")
    print("Then restart Claude Code.")


if __name__ == "__main__":
    main()
