from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class NotificationModel(Base):
    __tablename__ = 'notifications'
    __table_args__ = (
        UniqueConstraint(
            'notice_id', 'channel', name='uq_notifications_notice_id_channel'
        ),
    )

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    notice_id: Mapped[UUID] = mapped_column()
    user_uuid: Mapped[UUID] = mapped_column()
    channel: Mapped[str] = mapped_column(String(20))
    destination: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(250))
    body: Mapped[str] = mapped_column(String(4000))
    status: Mapped[str] = mapped_column(String(20))
    attempts: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
