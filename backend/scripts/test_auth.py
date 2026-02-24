"""
Test JWT auth flow: register, login, /auth/me, list documents.
Run from backend directory with server running:
  python -m scripts.test_auth
"""
import os
import sys

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.environ.get("API_BASE", "http://localhost:8000")

def main():
    import urllib.request
    import json

    def post(path, data):
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())

    def get(path, token):
        req = urllib.request.Request(
            f"{BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())

    print("1. Register...")
    try:
        user = post("/api/v1/auth/register", {
            "email": "testauth@example.com",
            "password": "securepass123",
            "full_name": "Test Auth User",
        })
        print("   User:", user.get("email"), user.get("id"))
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "already registered" in body:
            print("   (user already exists, continuing)")
        else:
            print("   Error:", e.code)
            try:
                err = json.loads(body)
                print("   detail:", err.get("detail", err))
                if err.get("traceback"):
                    print("   traceback:", err["traceback"][:800])
            except Exception:
                print("   Response body:", body[:500] if body else "(empty)")
            return
    except Exception as e:
        print("   Exception:", type(e).__name__, e)
        return

    print("2. Login (use same email/password as register)...")
    try:
        token_resp = post("/api/v1/auth/login", {
            "email": "testauth@example.com",
            "password": "securepass123",
        })
        token = token_resp["access_token"]
        print("   Got access_token (length %d)" % len(token))
    except urllib.error.HTTPError as e:
        print("   Error:", e.code, e.read().decode())
        return

    print("3. GET /api/v1/auth/me...")
    try:
        me = get("/api/v1/auth/me", token)
        print("   Me:", me.get("email"), me.get("full_name"))
    except urllib.error.HTTPError as e:
        print("   Error:", e.code, e.read().decode())
        return

    print("4. GET /api/v1/documents (with Bearer)...")
    try:
        docs = get("/api/v1/documents", token)
        print("   Documents count:", len(docs))
    except urllib.error.HTTPError as e:
        print("   Error:", e.code, e.read().decode())
        return

    print("Done. Use header: Authorization: Bearer <access_token>")

if __name__ == "__main__":
    main()
