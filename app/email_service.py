import os
import base64
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger("freshscan.email")
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
GMAIL_FROM_EMAIL = os.getenv("GMAIL_FROM_EMAIL", os.getenv("SMTP_FROM_EMAIL", "me"))

# SMTP Fallback Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "no-reply@freshscan.io")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]

def render_verification_html(full_name: str, code: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>FreshScan Email Verification</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #F8FAFC;
      margin: 0;
      padding: 24px;
      color: #0F172A;
    }}
    .container {{
      max-width: 520px;
      margin: 0 auto;
      background-color: #FFFFFF;
      border-radius: 20px;
      padding: 36px 32px;
      border: 1px solid #E2E8F0;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }}
    .badge {{
      display: inline-block;
      background-color: #ECFDF5;
      color: #0F4A2B;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.8px;
      padding: 6px 14px;
      border-radius: 9999px;
      margin-bottom: 20px;
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      color: #0F172A;
      margin: 0 0 10px 0;
      letter-spacing: -0.5px;
    }}
    p {{
      font-size: 15px;
      line-height: 22px;
      color: #64748B;
      margin: 0 0 24px 0;
    }}
    .code-box {{
      background-color: #F1F5F9;
      border: 2px dashed #CBD5E1;
      border-radius: 16px;
      padding: 20px;
      text-align: center;
      margin: 28px 0;
    }}
    .code {{
      font-size: 38px;
      font-weight: 900;
      letter-spacing: 10px;
      color: #0F4A2B;
      margin: 0;
    }}
    .code-hint {{
      font-size: 12px;
      font-weight: 700;
      color: #94A3B8;
      margin-top: 8px;
      letter-spacing: 0.5px;
    }}
    .footer {{
      border-top: 1px solid #F1F5F9;
      padding-top: 20px;
      margin-top: 28px;
      font-size: 12px;
      color: #94A3B8;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="badge">✦ LESS QUEUE. MORE YOU.</div>
    <h1>Verify your email</h1>
    <p>Hi {full_name or 'there'},</p>
    <p>Welcome to FreshScan! Enter this 6-digit verification code in the app to complete your registration and activate your account:</p>
    
    <div class="code-box">
      <div class="code">{code}</div>
      <div class="code-hint">EXPIRES IN 15 MINUTES</div>
    </div>

    <p>If you didn't create a FreshScan account, you can safely ignore this email.</p>

    <div class="footer">
      FreshScan AI · Automated Freshness & Scan-and-Go Grocery
    </div>
  </div>
</body>
</html>"""

def render_verification_text(full_name: str, code: str) -> str:
    return f"""Welcome to FreshScan!

Hi {full_name or 'there'},

Your 6-digit FreshScan email verification code is:

    {code}

This code will expire in 15 minutes. Enter it in the app to activate your account.

If you did not request this, please ignore this email.

FreshScan AI · Scan-and-Go Grocery
"""

def get_gmail_credentials() -> Credentials | None:
    """
    Loads Google OAuth2 credentials for the Gmail API.
    Checks environment variables first, then local token.json.
    """
    creds = None

    # 1. Check direct refresh token in environment variables
    if GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN:
        try:
            creds = Credentials(
                token=None,
                refresh_token=GMAIL_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GMAIL_CLIENT_ID,
                client_secret=GMAIL_CLIENT_SECRET,
                scopes=GMAIL_SCOPES,
            )
            creds.refresh(Request())
            return creds
        except Exception as e:
            logger.warning(f"Failed to refresh Gmail API credentials from .env: {e}")

    # 2. Check token.json file
    token_candidate_paths = [
        GMAIL_TOKEN_PATH,
        os.path.join(os.path.dirname(__file__), "..", "token.json"),
        os.path.join(os.getcwd(), "token.json"),
    ]
    for path in token_candidate_paths:
        if os.path.exists(path):
            try:
                creds = Credentials.from_authorized_user_file(path, GMAIL_SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                if creds and creds.valid:
                    return creds
            except Exception as e:
                logger.warning(f"Failed to load Gmail credentials from {path}: {e}")

    return None

def send_via_gmail_api(to_email: str, subject: str, html_content: str, text_content: str) -> dict:
    """
    Sends an email using the official Google Gmail REST API.
    """
    creds = get_gmail_credentials()
    if not creds:
        return {"sent": False, "reason": "No valid Gmail API credentials found"}

    try:
        message = MIMEMultipart("alternative")
        message["To"] = to_email
        message["From"] = GMAIL_FROM_EMAIL
        message["Subject"] = subject

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        raw_bytes = message.as_bytes()
        raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        send_result = service.users().messages().send(userId="me", body={"raw": raw_b64}).execute()

        msg_id = send_result.get("id", "")
        logger.info(f"Verification email successfully dispatched via Gmail API: message_id={msg_id}")
        return {"sent": True, "method": "gmail_api", "message_id": msg_id}
    except Exception as e:
        logger.error(f"Gmail API error while sending to {to_email}: {e}")
        return {"sent": False, "reason": str(e)}

def send_via_smtp(to_email: str, subject: str, html_content: str, text_content: str) -> dict:
    """
    Fallback transmission via standard SMTP if configured.
    """
    if not SMTP_HOST:
        return {"sent": False, "reason": "SMTP_HOST not configured"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            if SMTP_TLS:
                server.starttls()

        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)

        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Verification email successfully dispatched to {to_email} via SMTP ({SMTP_HOST})")
        return {"sent": True, "method": "smtp"}
    except Exception as e:
        logger.warning(f"SMTP dispatch failed: {e}")
        return {"sent": False, "reason": str(e)}

def send_verification_email(to_email: str, full_name: str, code: str) -> dict:
    """
    Dispatches verification code via Google Gmail API (priority 1),
    falling back to SMTP (priority 2), and terminal logger (priority 3).
    """
    subject = f"{code} is your FreshScan verification code"
    html_content = render_verification_html(full_name, code)
    text_content = render_verification_text(full_name, code)

    # 1. Print verification code prominently to console
    print("\n" + "=" * 65)
    print(f"📧 [FRESHSCAN EMAIL SERVICE - GMAIL API]")
    print(f"To: {full_name} <{to_email}>")
    print(f"Subject: {subject}")
    print(f"✦ VERIFICATION CODE: >>> {code} <<<")
    print(f"Expires in 15 minutes")
    print("=" * 65 + "\n")

    # 2. Attempt Google Gmail API transmission
    gmail_result = send_via_gmail_api(to_email, subject, html_content, text_content)
    if gmail_result.get("sent"):
        return {
            "success": True,
            "method": "gmail_api",
            "message_id": gmail_result.get("message_id"),
            "email": to_email,
            "code": code,
        }

    # 3. Attempt SMTP transmission fallback if Gmail API not yet authorized
    smtp_result = send_via_smtp(to_email, subject, html_content, text_content)
    if smtp_result.get("sent"):
        return {
            "success": True,
            "method": "smtp",
            "email": to_email,
            "code": code,
        }

    # 4. Fallback to console transmission
    return {
        "success": True,
        "method": "console",
        "email": to_email,
        "code": code,
        "gmail_api_note": gmail_result.get("reason"),
    }
