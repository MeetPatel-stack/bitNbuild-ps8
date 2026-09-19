import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("app.integrations.notification")


class NotificationProvider(ABC):
    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        title: str,
        message: str,
        channel: str = "SMS",
    ) -> Dict[str, Any]:
        """Send notification via specified channel."""
        pass


class MockNotificationProvider(NotificationProvider):
    async def send_message(
        self,
        recipient: str,
        title: str,
        message: str,
        channel: str = "SMS",
    ) -> Dict[str, Any]:
        logger.info(
            "MockNotificationProvider dispatched message via %s to %s | Title: '%s' | Body: '%s'",
            channel,
            recipient,
            title,
            message[:100],
        )
        return {
            "delivered": True,
            "channel": channel,
            "recipient": recipient,
            "provider_reference": f"mock-msg-{abs(hash(title + recipient)) % 1000000}",
            "status": "DELIVERED",
        }


mock_notification_provider = MockNotificationProvider()
