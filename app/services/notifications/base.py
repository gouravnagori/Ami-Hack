"""
Notification service — services/notifications/base.py

Thin adapter layer. Never block a request.
Adapters: console (always), SMS (Twilio-style, optional), email (SMTP, optional).
All sending is queued via ARQ; this module only defines the interface and console adapter.
"""

import structlog

logger = structlog.get_logger("goldenhour.notifications")

TEMPLATES: dict[str, str] = {
    "new_offer": "New food offer available: {portions} portions of {diet} food from {donor_name}.",
    "offer_expiring": "Your offer expires in {seconds}s. Accept now to claim the food.",
    "driver_assigned": "Driver {driver_name} is on the way. ETA: {eta_minutes} min.",
    "picked_up": "Food picked up from {donor_name}. Expected delivery at {eta}.",
    "delivered": "Delivery confirmed! {portions} meals delivered to {org_name}. Thank you!",
    "risk_alert": "ALERT: Allocation {allocation_id} is now {risk}. Reason: {reason}.",
    "otp_pickup": "GoldenHour pickup OTP: {otp}. Valid for 4 hours. Do not share.",
    "otp_dropoff": "GoldenHour delivery OTP: {otp}. Share this with the driver on arrival.",
}


def render_template(template_key: str, data: dict) -> str:
    """Render a notification template with data, returning a plain string."""
    tpl = TEMPLATES.get(template_key, template_key)
    try:
        return tpl.format(**data)
    except KeyError:
        return tpl


class NotificationService:
    """
    Facade for sending notifications.
    The base implementation logs to console (structlog).
    Subclasses or monkey-patching can override _send_sms / _send_email.
    """

    async def send(self, user_id: str, template: str, data: dict) -> None:
        """
        Non-blocking notification send. Falls back to console silently.
        In production this enqueues an ARQ job, not inline HTTP.
        """
        message = render_template(template, data)
        await self._send_console(user_id=user_id, template=template, message=message)

    async def _send_console(self, user_id: str, template: str, message: str) -> None:
        logger.info(
            "notification.console",
            user_id=user_id,
            template=template,
            message=message,
        )

    async def _send_sms(self, phone: str, message: str) -> None:
        """Twilio-style SMS stub. Override with live adapter when SMS_ENABLED=true."""
        logger.info("notification.sms_stub", phone=phone[:4] + "****", message=message)

    async def _send_email(self, email: str, subject: str, body: str) -> None:
        """SMTP stub. Override with live adapter when EMAIL_ENABLED=true."""
        logger.info("notification.email_stub", email=email, subject=subject)


# Module-level singleton used by API handlers and ARQ workers.
notification_service = NotificationService()
