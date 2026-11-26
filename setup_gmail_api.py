#!/usr/bin/env python3
"""
FreshScan Gmail API Setup & Authorization Utility

This script authorizes FreshScan to send verification emails directly
through the official Google Gmail API (OAuth 2.0).

Usage:
1. Go to Google Cloud Console (https://console.cloud.google.com/).
2. Create or select a project, then enable the "Gmail API".
3. Under "APIs & Services" > "Credentials", click "Create Credentials" > "OAuth client ID".
   - Application type: "Desktop app"
   - Name: "FreshScan Backend"
4. Download the JSON file and save it in this directory as `credentials.json`
   (or provide client ID and Secret when prompted).
5. Run:
   python setup_gmail_api.py

The script will open your browser for 1-click Google authorization and
automatically save `token.json` and update your `.env` file!
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
ENV_FILE = ".env"

def main():
    print("=" * 65)
    print("🚀 FreshScan Gmail API Authorization Setup")
    print("=" * 65)

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\n⚠️  {CREDENTIALS_FILE} not found in current directory.")
        print("To authenticate:")
        print("1. Download your OAuth client JSON from Google Cloud Console.")
        print(f"2. Rename it to '{CREDENTIALS_FILE}' and place it in '{os.getcwd()}'.")
        print("3. Re-run: python setup_gmail_api.py\n")
        return

    print(f"\n✓ Found {CREDENTIALS_FILE}. Starting OAuth2 authorization flow...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    # Save credentials to token.json
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    print(f"✓ Saved authorized token to {TOKEN_FILE}")

    # Extract info
    token_data = json.loads(creds.to_json())
    client_id = token_data.get("client_id", "")
    client_secret = token_data.get("client_secret", "")
    refresh_token = token_data.get("refresh_token", "")

    print("\n✅ Gmail API authorization successful!")
    print(f"Client ID: {client_id[:12]}...")
    print(f"Refresh Token: {refresh_token[:12]}...")

    # Update .env if present
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            env_content = f.read()

        updates = {
            "GMAIL_CLIENT_ID": client_id,
            "GMAIL_CLIENT_SECRET": client_secret,
            "GMAIL_REFRESH_TOKEN": refresh_token,
            "USE_GMAIL_API": "true",
        }

        for k, v in updates.items():
            if f"{k}=" in env_content:
                lines = env_content.splitlines()
                lines = [f"{k}={v}" if line.startswith(f"{k}=") else line for line in lines]
                env_content = "\n".join(lines)
            else:
                env_content += f"\n{k}={v}"

        with open(ENV_FILE, "w") as f:
            f.write(env_content)
        print(f"✓ Automatically saved Gmail API credentials into {ENV_FILE}")

    print("\nAll done! FreshScan will now send emails via the official Gmail API.")

if __name__ == "__main__":
    main()
