#!/usr/bin/env python3
"""Send a one-off test email via Resend. Does not touch scheduler or reminder logic.
Usage (from backend dir):
  python scripts/send_test_email.py
  python scripts/send_test_email.py your@email.com
  TEST_EMAIL=your@email.com python scripts/send_test_email.py
Recipient is taken from: TEST_EMAIL env, first argument, or .env smtp_to (if set).
"""

import os
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))


def main() -> int:
    from app.core.config import get_settings
    from app.services.email_service import send_email

    to_email = (
        os.environ.get("TEST_EMAIL", "").strip()
        or (sys.argv[1] if len(sys.argv) > 1 else "")
        or (get_settings().smtp_to or "").strip()
    )
    if not to_email:
        print("No recipient. Set TEST_EMAIL in .env, or run: python scripts/send_test_email.py your@email.com")
        return 1
    subject = "Complynexa – Resend test"
    html = """
    <h2>Resend integration test</h2>
    <p>This is a test email from the Complynexa backend.</p>
    <p>If you received this, Resend is configured correctly.</p>
    <p>— Complynexa</p>
    """
    success, result = send_email(to_email, subject, html)
    if success:
        print(f"Test email sent to {to_email}")
        # Resend returns {"id": "..."} on success; useful to check in Resend dashboard
        if isinstance(result, dict) and result.get("id"):
            print(f"Resend email id: {result['id']} (check https://resend.com/emails if not received)")
        print(
            "If you didn't receive it: (1) Check spam. (2) In Resend dashboard, verify the "
            "recipient email for development/sandbox delivery."
        )
        return 0
    print(f"Failed: {result}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
