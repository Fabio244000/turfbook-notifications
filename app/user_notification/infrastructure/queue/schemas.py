from uuid import UUID

from pydantic import BaseModel

from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.ports.input.send_notice_port import (
    SendNoticeCommand,
)


class RecipientMessage(BaseModel):
    uuid: UUID
    email: str | None = None
    cellphone: str | None = None
    first_name: str | None = None


class NoticeMessage(BaseModel):
    """The structure of the contract's notice (§5): types and enum values. Its rules
    (lengths, patterns, required contacts) are the domain's."""

    notice_id: UUID
    notifiers: list[Channel]
    recipient: RecipientMessage
    subject: str
    body: str

    def to_command(self) -> SendNoticeCommand:
        return SendNoticeCommand(
            notice_id=self.notice_id,
            channels=tuple(self.notifiers),
            recipient_uuid=self.recipient.uuid,
            subject=self.subject,
            body=self.body,
            email=self.recipient.email,
            cellphone=self.recipient.cellphone,
            first_name=self.recipient.first_name,
        )
