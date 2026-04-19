"""
OTP Service — Gmail SMTP based email verification.
Generates a 6-digit OTP, sends it via Gmail, stores it in session state.

Setup required (one time):
  1. Go to your Gmail account → Google Account → Security
  2. Enable 2-Step Verification
  3. Search "App Passwords" → Generate one for "Mail"
  4. Copy the 16-char app password
  5. Set it in config.py:
       GMAIL_SENDER  = "youremail@gmail.com"
       GMAIL_APP_PWD = ""
"""

import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from config import GMAIL_SENDER, GMAIL_APP_PWD
except ImportError:
    GMAIL_SENDER  = ""
    GMAIL_APP_PWD = ""


# ── OTP store (in-memory, keyed by email) ──────────────────────────────
# Structure: { email: { "otp": "123456", "expires_at": timestamp } }
_otp_store: dict = {}

OTP_EXPIRY_SECONDS = 300   # 5 minutes


def generate_otp() -> str:
    """Returns a 6-digit OTP string."""
    return str(random.randint(100000, 999999))


def send_otp_email(to_email: str) -> tuple[bool, str]:
    """
    Generates OTP, stores it, and sends via Gmail SMTP.
    Returns (success: bool, message: str)
    """
    if not GMAIL_SENDER or not GMAIL_APP_PWD:
        return False, "Email service not configured. Please set GMAIL_SENDER and GMAIL_APP_PWD in config.py"

    otp = generate_otp()
    _otp_store[to_email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS
    }

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Verification Code — AI Role Recommendation"
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = to_email

    html_body = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;background:#0D1B4B;margin:0;padding:0">
      <div style="max-width:480px;margin:40px auto;background:#1E2761;border-radius:18px;overflow:hidden">
        <div style="background:#4FC3F7;padding:24px 32px">
          <h2 style="margin:0;color:#0D1B4B;font-size:22px">🚀 AI Role Recommendation Suite</h2>
        </div>
        <div style="padding:32px">
          <p style="color:#CADCFC;font-size:16px;margin-top:0">
            Here is your one-time verification code:
          </p>
          <div style="background:#0D1B4B;border-radius:14px;padding:24px;text-align:center;
                      border:2px solid #4FC3F7;margin:24px 0">
            <span style="font-size:42px;font-weight:900;letter-spacing:14px;color:#4FC3F7">
              {otp}
            </span>
          </div>
          <p style="color:#8899BB;font-size:13px">
            ⏱️ This code expires in <strong style="color:#FFB74D">5 minutes</strong>.<br>
            If you did not request this, you can safely ignore this email.
          </p>
        </div>
        <div style="background:#0D1B4B;padding:16px 32px;text-align:center">
          <p style="color:#8899BB;font-size:11px;margin:0">
            AI-Driven Intelligent Skill-Based Role Recommendation System
          </p>
        </div>
      </div>
    </body></html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PWD)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())
        return True, f"OTP sent to {to_email}. Check your inbox."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check your App Password in config.py"
    except smtplib.SMTPException as e:
        return False, f"Email send failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def verify_otp(email: str, entered_otp: str) -> tuple[bool, str]:
    """
    Verifies the OTP entered by user.
    Returns (valid: bool, message: str)
    """
    record = _otp_store.get(email)

    if not record:
        return False, "No OTP found for this email. Please request a new one."

    if time.time() > record["expires_at"]:
        del _otp_store[email]
        return False, "OTP has expired. Please request a new one."

    if entered_otp.strip() != record["otp"]:
        return False, "Incorrect OTP. Please try again."

    # Valid — clear it so it can't be reused
    del _otp_store[email]
    return True, "Email verified successfully!"


def clear_otp(email: str):
    """Clears OTP for an email (e.g. on cancel)."""
    _otp_store.pop(email, None)


def otp_exists(email: str) -> bool:
    """Returns True if a valid (non-expired) OTP exists for this email."""
    record = _otp_store.get(email)
    if not record:
        return False
    if time.time() > record["expires_at"]:
        del _otp_store[email]
        return False
    return True


def seconds_remaining(email: str) -> int:
    """Returns seconds until OTP expires (0 if not found/expired)."""
    record = _otp_store.get(email)
    if not record:
        return 0
    remaining = int(record["expires_at"] - time.time())
    return max(0, remaining)

# ══════════════════════════════════════════════════════════════════════
# APPLICATION STATUS EMAIL NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════

# Status configs: emoji, subject, header color, message
_STATUS_CONFIG = {
    "Shortlisted": {
        "emoji":   "⭐",
        "subject": "You've been Shortlisted!",
        "color":   "#F59E0B",
        "heading": "You've been Shortlisted!",
        "body":    "Great news! The employer has reviewed your profile and shortlisted you for further consideration. Your skills stood out from the competition.",
        "action":  "Keep an eye on your email — the employer may reach out to you soon for the next steps.",
    },
    "Interview": {
        "emoji":   "📅",
        "subject": "Interview Invitation!",
        "color":   "#A78BFA",
        "heading": "You've Been Invited for an Interview!",
        "body":    "Congratulations! The employer is impressed with your profile and would like to invite you for an interview.",
        "action":  "Prepare well — visit the Interview Prep section on Skill Match AI to practise role-specific questions.",
    },
    "Selected": {
        "emoji":   "🎉",
        "subject": "Congratulations — You're Selected!",
        "color":   "#00C896",
        "heading": "You Have Been Selected!",
        "body":    "We are thrilled to inform you that you have been <strong>selected</strong> for this role! The employer has chosen you from all applicants.",
        "action":  "Log in to Skill Match AI and check your Applications tab for further details from the employer.",
    },
    "Rejected": {
        "emoji":   "📋",
        "subject": "Update on Your Application",
        "color":   "#94A3B8",
        "heading": "Application Status Update",
        "body":    "Thank you for applying. After careful consideration, the employer has decided to move forward with other candidates for this role.",
        "action":  "Don't be discouraged! Visit Skill Match AI to explore more matching opportunities and keep improving your profile.",
    },
}


def send_status_notification(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    company: str,
    new_status: str,
    employer_comment: str = "",
) -> tuple[bool, str]:
    """
    Sends a branded status notification email to the candidate.
    Called from applications_store.update_application_status().
    Only sends for: Shortlisted, Interview, Selected, Rejected.
    Returns (success: bool, message: str).
    """
    if not GMAIL_SENDER or not GMAIL_APP_PWD:
        return False, "Email service not configured in config.py"

    cfg = _STATUS_CONFIG.get(new_status)
    if not cfg:
        return False, f"No email template for status: {new_status}"

    # ── Build HTML email ─────────────────────────────────────────────
    comment_block = ""
    if employer_comment and employer_comment.strip():
        comment_block = f"""
        <div style="background:#0D1B4B;border-radius:10px;padding:16px 20px;margin:20px 0;
                    border-left:4px solid {cfg['color']}">
            <div style="font-size:12px;color:#8899BB;margin-bottom:6px;text-transform:uppercase;
                        letter-spacing:0.5px">Employer's Message</div>
            <div style="color:#CADCFC;font-size:14px;line-height:1.6;font-style:italic">
                "{employer_comment.strip()}"
            </div>
        </div>"""

    html_body = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;background:#0D1B4B;margin:0;padding:0">
      <div style="max-width:520px;margin:40px auto;background:#1E2761;border-radius:18px;
                  overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.4)">

        <!-- Header -->
        <div style="background:{cfg['color']};padding:24px 32px;text-align:center">
          <div style="font-size:40px;margin-bottom:8px">{cfg['emoji']}</div>
          <h2 style="margin:0;color:#0D1B4B;font-size:20px;font-weight:800">
            {cfg['heading']}
          </h2>
        </div>

        <!-- Body -->
        <div style="padding:28px 32px">

          <p style="color:#CADCFC;font-size:15px;margin-top:0">
            Hi <strong style="color:#FFFFFF">{candidate_name}</strong>,
          </p>

          <!-- Job card -->
          <div style="background:#0D1B4B;border-radius:12px;padding:16px 20px;margin:16px 0;
                      border:1px solid rgba(79,195,247,0.3)">
            <div style="font-size:16px;font-weight:700;color:#FFFFFF;margin-bottom:4px">
              {job_title}
            </div>
            <div style="font-size:13px;color:#8899BB">
              🏢 {company}
            </div>
            <div style="margin-top:10px">
              <span style="background:{cfg['color']}22;color:{cfg['color']};
                           border:1px solid {cfg['color']}55;padding:3px 12px;
                           border-radius:99px;font-size:12px;font-weight:700;
                           text-transform:uppercase;letter-spacing:0.5px">
                {new_status}
              </span>
            </div>
          </div>

          <p style="color:#CADCFC;font-size:14px;line-height:1.7">
            {cfg['body']}
          </p>

          {comment_block}

          <p style="color:#8899BB;font-size:13px;line-height:1.6">
            {cfg['action']}
          </p>

          <!-- CTA Button -->
          <div style="text-align:center;margin:28px 0 12px">
            <a href="#" style="background:{cfg['color']};color:#0D1B4B;padding:12px 32px;
               border-radius:10px;text-decoration:none;font-weight:800;font-size:14px;
               display:inline-block">
              View My Applications →
            </a>
          </div>

        </div>

        <!-- Footer -->
        <div style="background:#0D1B4B;padding:16px 32px;text-align:center">
          <p style="color:#8899BB;font-size:11px;margin:0">
            Skill Match AI &nbsp;·&nbsp; AI-Driven Job Recommendation Platform
          </p>
          <p style="color:#8899BB;font-size:10px;margin:6px 0 0">
            You received this email because you applied for a job on Skill Match AI.
          </p>
        </div>

      </div>
    </body></html>
    """

    # ── Send via Gmail SMTP ──────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{cfg['emoji']} {cfg['subject']} — {job_title} at {company}"
    msg["From"]    = f"Skill Match AI <{GMAIL_SENDER}>"
    msg["To"]      = candidate_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PWD)
            server.sendmail(GMAIL_SENDER, candidate_email, msg.as_string())
        return True, f"Notification sent to {candidate_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check GMAIL_APP_PWD in config.py"
    except Exception as e:
        return False, f"Email send failed: {str(e)}"