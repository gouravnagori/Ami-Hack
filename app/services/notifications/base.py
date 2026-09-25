"""
Notification service — services/notifications/base.py

Unified notification dispatcher. Routes notifications to:
- Console (always, for logging)
- SMTP Email (when SMTP_ENABLED=true and user has email)
- WebSocket (real-time, always)

All sending is non-blocking.
"""

import asyncio
import structlog

from app.core.config import settings

logger = structlog.get_logger("goldenhour.notifications")

TEMPLATES: dict[str, str] = {
    "new_offer": "New food offer available: {portions} portions of {diet} food from {donor_name}.",
    "offer_expiring": "Your offer expires in {seconds}s. Accept now to claim the food.",
    "offer_accepted": "Offer accepted! {portions} portions will be delivered to {org_name}.",
    "driver_assigned": "Driver {driver_name} is on the way. ETA: {eta_minutes} min.",
    "picked_up": "Food picked up from {donor_name}. Expected delivery at {eta}.",
    "delivered": "Delivery confirmed! {portions} meals delivered to {org_name}. Thank you!",
    "risk_alert": "ALERT: Allocation {allocation_id} is now {risk}. Reason: {reason}.",
    "otp_pickup": "GoldenHour pickup OTP: {otp}. Valid for 4 hours. Do not share.",
    "otp_dropoff": "GoldenHour delivery OTP: {otp}. Share this with the driver on arrival.",
    "welcome": "Welcome to GoldenHour, {role}! Your account is ready.",
    "donation_posted": "Your donation of {portions} portions ({diet}) has been posted and is being matched.",
    "email_verification": "Your GoldenHour email verification code is: {otp}. Valid for 10 minutes.",
    "login_otp": "Your GoldenHour login verification code is: {otp}. Valid for 10 minutes.",
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
    Unified notification dispatcher.
    Sends to console (always) + email (when configured) + WebSocket (when available).
    """

    def __init__(self):
        self._email_service = None

    def _get_email_service(self):
        """Lazy import to avoid circular imports."""
        if self._email_service is None:
            from app.services.notifications.email import email_service
            self._email_service = email_service
        return self._email_service

    async def send(
        self,
        user_id: str,
        template: str,
        data: dict,
        email: str | None = None,
    ) -> None:
        """
        Send notification through all available channels.
        - Always logs to console
        - Sends email if SMTP is enabled and email address is provided
        - Emits WebSocket event if user is connected
        """
        message = render_template(template, data)

        # 1. Console log (always)
        await self._send_console(user_id=user_id, template=template, message=message)

        # 2. Email (if configured and email provided) - fire and forget, non-blocking
        if email and settings.SMTP_ENABLED:
            async def _send_email_async():
                try:
                    email_svc = self._get_email_service()
                    await asyncio.wait_for(
                        email_svc.send_email(to_email=email, template_key=template, data=data),
                        timeout=6.0,
                    )
                except Exception as e:
                    logger.error("notification.email_error", user_id=user_id, error=str(e))

            asyncio.create_task(_send_email_async())

        # 3. WebSocket (if user is connected)
        try:
            from app.ws import manager
            await manager.send_to_user(user_id, f"notification.{template}", {
                "message": message,
                "template": template,
                "data": data,
            })
        except Exception:
            pass  # User may not be connected

    async def _send_console(self, user_id: str, template: str, message: str) -> None:
        logger.info(
            "notification.sent",
            user_id=user_id,
            template=template,
            message=message,
        )

    async def notify_new_offer(
        self, user_id: str, email: str | None, portions: int, diet: str, donor_name: str
    ) -> None:
        await self.send(user_id, "new_offer", {
            "portions": portions, "diet": diet, "donor_name": donor_name,
        }, email=email)

    async def notify_offer_accepted(
        self, user_id: str, email: str | None, portions: int, org_name: str
    ) -> None:
        await self.send(user_id, "offer_accepted", {
            "portions": portions, "org_name": org_name,
        }, email=email)

    async def notify_driver_assigned(
        self, user_id: str, email: str | None, driver_name: str, eta_minutes: int
    ) -> None:
        await self.send(user_id, "driver_assigned", {
            "driver_name": driver_name, "eta_minutes": eta_minutes,
        }, email=email)

    async def notify_delivered(
        self, user_id: str, email: str | None, portions: int, org_name: str
    ) -> None:
        await self.send(user_id, "delivered", {
            "portions": portions, "org_name": org_name,
        }, email=email)

    async def notify_risk_alert(
        self, user_id: str, email: str | None, allocation_id: str, risk: str, reason: str
    ) -> None:
        await self.send(user_id, "risk_alert", {
            "allocation_id": allocation_id, "risk": risk, "reason": reason,
        }, email=email)

    async def notify_welcome(self, user_id: str, email: str | None, role: str) -> None:
        await self.send(user_id, "welcome", {"role": role}, email=email)

    async def notify_donation_posted(
        self, user_id: str, email: str | None, portions: int, diet: str
    ) -> None:
        await self.send(user_id, "donation_posted", {
            "portions": portions, "diet": diet,
        }, email=email)


# Module-level singleton
notification_service = NotificationService()
