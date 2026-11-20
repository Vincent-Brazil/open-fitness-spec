"""Run: python passport_quickstart.py YOUR_CLIENT_ID signin|settings|ride|history"""
import argparse
import base64
import hashlib
import hmac
import json
import re
import secrets
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PASSPORT = "https://openfitness.apogee.training"
PORT = 8765
SCOPES = {"settings": "ftp", "ride": "write", "history": "history"}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(base, path, *, token=None, form=None, payload=None):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        data = urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = Request(base + path, data=data, headers=headers)
    try:
        with build_opener(NoRedirect()).open(req, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        with error:
            raise RuntimeError(f"{path.split('?')[0]} returned HTTP {error.code}. See the quickstart's error table.") from None


def connect(base, client_id, scope, port):
    identity_only = scope is None
    path_prefix = "/signin" if identity_only else "/oauth"
    callback_path = "/signin/callback" if identity_only else "/callback"
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Keep the single-use authorization code out of request logs.

        def do_GET(self):
            path = urlsplit(self.path)
            if path.path != callback_path:
                self.send_error(404)
                return
            params = parse_qs(path.query)
            if len(params.get("state", [])) != 1 or any(len(params.get(k, [])) > 1 for k in ("code", "error")):
                self.send_error(400, "Invalid callback")
                return
            returned_state = params["state"][0]
            if not hmac.compare_digest(returned_state.encode(), state.encode()):
                self.send_error(400, "Connection attempt did not match")
                return
            result.update(code=params.get("code", [""])[0], error=params.get("error", [""])[0])
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(b"Return to your terminal to see the result.")

    with HTTPServer(("127.0.0.1", port), Callback) as listener:
        callback = f"http://127.0.0.1:{listener.server_port}{callback_path}"
        params = dict(client_id=client_id, redirect_uri=callback, state=state,
                      code_challenge_method="S256", code_challenge=challenge)
        params.update({"response_type": "code"} if identity_only else {"scope": scope})
        url = base + path_prefix + "/authorize?" + urlencode(params)
        print("Continue in your browser. Open this URL if needed:\n" + url)
        webbrowser.open(url)
        deadline = time.monotonic() + 300
        listener.timeout = 1
        while not result and time.monotonic() < deadline:
            listener.handle_request()
    if not result:
        raise RuntimeError("The connection timed out. Check the registered callback and run again.")
    if result["error"] or not result["code"]:
        raise RuntimeError("Connection declined or cancelled.")
    return call(base, path_prefix + "/token", form=dict(grant_type="authorization_code", client_id=client_id,
                redirect_uri=callback, code=result["code"], code_verifier=verifier))


def run(base, client_id, mode, port=PORT):
    if mode == "signin":
        identity = connect(base, client_id, None, port)
        if (identity.get("iss") != base or identity.get("aud") != client_id
                or not re.fullmatch(r"[A-Za-z0-9_-]{32}", identity.get("sub", ""))):
            raise RuntimeError("Unexpected sign-in response.")
        # Look up (iss, aud, sub) in your own accounts, then create your app session.
        print("Passport identity verified for this app. No training permissions requested.")
        return
    grant = connect(base, client_id, SCOPES[mode], port)
    if SCOPES[mode] not in grant["scope"].split():
        print("Permission was left unchecked. No activity or training data was exchanged.")
        return
    token = grant["access_token"]  # This example holds the token in memory for one run.
    if mode == "settings":
        shared = call(base, "/v1/training", token=token)["shared"]
        print(f"Passport FTP: {shared['ftp']:g} W" if "ftp" in shared else "No FTP set. Keep the app's current setting.")
    elif mode == "ride":
        # A fixed test recording makes a second run safe to replay with this rider and client.
        ride = {"source_ride_id": "quickstart-ride-001", "started": "2026-01-15T09:00:00Z",
                "duration": 900, "distance": 6000, "power": 180}
        for _ in range(2):
            print(call(base, "/v1/activities", token=token, payload=ride))
    else:
        cursor = 0
        while True:
            page = call(base, f"/v1/history?after={cursor}&limit=100", token=token)
            for ride in page["rides"]:
                print(ride["id"], ride["started"], ride["label"], ride["duration"], "s")
            cursor = page["next_cursor"]
            if not page["has_more"]:
                print("Caught up. Next sync cursor:", cursor)
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Try one Open Fitness capability with a test rider.")
    parser.add_argument("client_id")
    parser.add_argument("mode", choices=["signin", *SCOPES])
    parser.add_argument("--local", action="store_true", help="Use the local passport on port 5810")
    args = parser.parse_args()
    try:
        run("http://127.0.0.1:5810" if args.local else PASSPORT, args.client_id, args.mode)
    except (OSError, RuntimeError) as error:
        sys.exit(str(error))
