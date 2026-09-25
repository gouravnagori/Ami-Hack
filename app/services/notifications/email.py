"""
SMTP Email Service — services/notifications/email.py

Real email sending via SMTP with HTML templates for different notification types.
Falls back to console logging when SMTP is disabled or unavailable.
"""

import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger("goldenhour.email")


# ── HTML Email Templates ──

def _base_html(title: str, content: str) -> str:
    """Wrap content in a clean, branded HTML email template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f7f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7f5;padding:30px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <tr><td style="background:#1a3c34;padding:24px 32px;text-align:center;">
    <span style="font-size:28px;">⏳</span>
    <h1 style="color:#b8f275;font-size:20px;margin:8px 0 0;font-weight:800;">{title}</h1>
  </td></tr>
  <tr><td style="padding:28px 32px;color:#1a3c34;font-size:15px;line-height:1.6;">
    {content}
  </td></tr>
  <tr><td style="padding:16px 32px;background:#f9faf8;border-top:1px solid #e8ece9;font-size:12px;color:#8a9a8e;text-align:center;">
    GoldenHour Food Rescue Platform &middot; Reducing food waste, one meal at a time
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


EMAIL_TEMPLATES: dict[str, dict[str, str]] = {
    "new_offer": {
        "subject": "🍲 New Food Offer Available — {portions} portions",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">New Food Offer!</h2>
<p><strong>{portions} portions</strong> of <strong>{diet}</strong> food from <strong>{donor_name}</strong> are available for rescue.</p>
<p style="margin:16px 0;"><a href="#" style="background:#b8f275;color:#1a3c34;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;display:inline-block;">View & Accept Offer</a></p>
<p style="color:#8a9a8e;font-size:13px;">This offer will expire soon. Act quickly to rescue this food!</p>"""
    },
    "offer_accepted": {
        "subject": "✅ Offer Accepted — Rescue confirmed",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Offer Accepted!</h2>
<p>Your food donation of <strong>{portions} portions</strong> has been accepted by <strong>{org_name}</strong>.</p>
<p>A driver will be assigned shortly for pickup.</p>"""
    },
    "driver_assigned": {
        "subject": "🛵 Driver Assigned — ETA {eta_minutes} min",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Driver On The Way!</h2>
<p>Driver <strong>{driver_name}</strong> has been assigned to pick up your donation.</p>
<p><strong>Estimated arrival:</strong> {eta_minutes} minutes</p>
<p style="color:#8a9a8e;font-size:13px;">Pickup OTP will be shared with the driver.</p>"""
    },
    "picked_up": {
        "subject": "📦 Food Picked Up — In transit",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Pickup Confirmed!</h2>
<p>Food has been picked up from <strong>{donor_name}</strong>.</p>
<p><strong>Expected delivery:</strong> {eta}</p>"""
    },
    "delivered": {
        "subject": "🎉 Delivery Confirmed — {portions} meals rescued!",
        "body": """<h2 style="color:#b8f275;margin:0 0 12px;background:#1a3c34;padding:16px;border-radius:8px;text-align:center;">🎉 Delivery Confirmed!</h2>
<p><strong>{portions} meals</strong> have been delivered to <strong>{org_name}</strong>.</p>
<p>Thank you for rescuing food and reducing waste!</p>"""
    },
    "risk_alert": {
        "subject": "⚠️ Risk Alert — Allocation {allocation_id}",
        "body": """<h2 style="color:#e74c3c;margin:0 0 12px;">⚠️ Risk Alert</h2>
<p>Allocation <strong>{allocation_id}</strong> status: <strong style="color:#e74c3c;">{risk}</strong></p>
<p>Reason: {reason}</p>"""
    },
    "otp_pickup": {
        "subject": "🔐 Your Pickup OTP — GoldenHour",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Pickup Verification Code</h2>
<div style="text-align:center;margin:20px 0;"><span style="font-size:32px;font-weight:800;letter-spacing:8px;background:#f4f7f5;padding:16px 32px;border-radius:8px;display:inline-block;">{otp}</span></div>
<p style="color:#8a9a8e;font-size:13px;">Valid for 4 hours. Do not share this code.</p>"""
    },
    "welcome": {
        "subject": "Welcome to GoldenHour — Let's rescue food together!",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Welcome to GoldenHour! 🌿</h2>
<p>Thank you for joining the food rescue network. Your role: <strong>{role}</strong></p>
<p>Together, we can make sure no prepared food goes to waste.</p>"""
    },
    "donation_posted": {
        "subject": "📋 Donation Posted — Matching in progress",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Donation Posted!</h2>
<p>Your donation of <strong>{portions} portions</strong> ({diet}) has been posted.</p>
<p>Our system is now matching it with nearby shelters and assigning drivers.</p>
<p style="color:#8a9a8e;font-size:13px;">You'll be notified once a recipient accepts.</p>"""
    },
    "email_verification": {
        "subject": "🔐 Verify your GoldenHour Account — Code: {otp}",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">Confirm Your Email Address</h2>
<p>Thank you for joining GoldenHour!</p>
<p>Please enter the following 6-digit verification code to activate your account:</p>
<div style="text-align:center;margin:24px 0;"><span style="font-size:36px;font-weight:800;letter-spacing:10px;background:#eef6ea;color:#1a3c34;padding:16px 32px;border-radius:10px;border:2px solid #b8f275;display:inline-block;">{otp}</span></div>
<p style="color:#8a9a8e;font-size:13px;text-align:center;">This code expires in 10 minutes. If you did not request this, please disregard this email.</p>"""
    },
    "login_otp": {
        "subject": "🔐 Your GoldenHour Login Code — Code: {otp}",
        "body": """<h2 style="color:#1a3c34;margin:0 0 12px;">GoldenHour One-Time Login Code</h2>
<p>Here is your one-time verification code to sign into your GoldenHour account:</p>
<div style="text-align:center;margin:24px 0;"><span style="font-size:36px;font-weight:800;letter-spacing:10px;background:#eef6ea;color:#1a3c34;padding:16px 32px;border-radius:10px;border:2px solid #b8f275;display:inline-block;">{otp}</span></div>
<p style="color:#8a9a8e;font-size:13px;text-align:center;">This code expires in 10 minutes. Never share your verification code with anyone.</p>"""
    },
}


class SMTPEmailService:
    """Real SMTP email sender with HTML templates and graceful fallback."""

    def __init__(self):
        self._enabled = settings.SMTP_ENABLED
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._user = settings.SMTP_USER
        self._password = settings.SMTP_PASSWORD
        self._from_email = settings.SMTP_FROM_EMAIL
        self._from_name = settings.SMTP_FROM_NAME
        self._use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        to_email: str,
        template_key: str,
        data: dict,
        subject_override: Optional[str] = None,
    ) -> bool:
        """
        Send an HTML email using a template.
        Returns True if sent, False if failed/disabled.
        """
        template = EMAIL_TEMPLATES.get(template_key)
        if not template:
            logger.warning("email.unknown_template", key=template_key)
            return False

        try:
            subject = (subject_override or template["subject"]).format(**data)
            body_html = _base_html(
                title="GoldenHour",
                content=template["body"].format(**data),
            )
        except KeyError as e:
            logger.warning("email.template_render_error", key=template_key, missing=str(e))
            return False

        if not self._enabled or not self._host:
            logger.info(
                "email.disabled_or_not_configured",
                to=to_email,
                subject=subject,
                template=template_key,
            )
            return False

        # Send via SMTP in a thread to avoid blocking the event loop
        return await asyncio.to_thread(
            self._send_sync, to_email, subject, body_html
        )

    def _send_sync(self, to_email: str, subject: str, html_body: str) -> bool:
        """Synchronous SMTP send — called from asyncio.to_thread."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self._from_name} <{self._from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # Plain text fallback
            import html as html_lib
            plain = html_lib.unescape(html_body.replace("<br>", "\n").replace("</p>", "\n"))
            import re
            plain = re.sub(r"<[^>]+>", "", plain)
            msg.attach(MIMEText(plain, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            if self._use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self._host, self._port, timeout=5) as server:
                    server.starttls(context=context)
                    server.login(self._user, self._password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self._host, self._port, timeout=5) as server:
                    if self._user:
                        server.login(self._user, self._password)
                    server.send_message(msg)

            logger.info("email.sent", to=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("email.send_failed", to=to_email, error=str(e))
            return False

    async def send_welcome(self, to_email: str, role: str) -> bool:
        return await self.send_email(to_email, "welcome", {"role": role})

    async def send_new_offer(self, to_email: str, portions: int, diet: str, donor_name: str) -> bool:
        return await self.send_email(to_email, "new_offer", {"portions": portions, "diet": diet, "donor_name": donor_name})

    async def send_offer_accepted(self, to_email: str, portions: int, org_name: str) -> bool:
        return await self.send_email(to_email, "offer_accepted", {"portions": portions, "org_name": org_name})

    async def send_driver_assigned(self, to_email: str, driver_name: str, eta_minutes: int) -> bool:
        return await self.send_email(to_email, "driver_assigned", {"driver_name": driver_name, "eta_minutes": eta_minutes})

    async def send_picked_up(self, to_email: str, donor_name: str, eta: str) -> bool:
        return await self.send_email(to_email, "picked_up", {"donor_name": donor_name, "eta": eta})

    async def send_delivered(self, to_email: str, portions: int, org_name: str) -> bool:
        return await self.send_email(to_email, "delivered", {"portions": portions, "org_name": org_name})

    async def send_risk_alert(self, to_email: str, allocation_id: str, risk: str, reason: str) -> bool:
        return await self.send_email(to_email, "risk_alert", {"allocation_id": allocation_id, "risk": risk, "reason": reason})

    async def send_donation_posted(self, to_email: str, portions: int, diet: str) -> bool:
        return await self.send_email(to_email, "donation_posted", {"portions": portions, "diet": diet})


# Singleton
email_service = SMTPEmailService()
