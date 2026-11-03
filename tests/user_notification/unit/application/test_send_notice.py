import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.user_notification.application.use_cases.send_notice import (
    SendNoticeUseCase,
)
from app.user_notification.domain.entities.channel import Channel
from app.user_notification.domain.entities.notification import (
    Notification,
    NotificationStatus,
)
from app.user_notification.domain.exceptions import (
    DeliveryRejectedError,
    DeliveryUnavailableError,
    InvalidNoticeError,
)
from app.user_notification.domain.ports.input.send_notice_port import (
    SendNoticeCommand,
)
from tests.fakes.user_notification import (
    FakeChannelSender,
    FakeClock,
    FakeUnitOfWork,
)

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
EMAIL = 'luis.h@gmail.com'
CELLPHONE = '+51987654321'
SUBJECT = 'Tu cuenta de TurfBook fue bloqueada'
BODY = 'Hola Luis, tu cuenta de TurfBook fue bloqueada por 5 intentos fallidos.'


def _command(**overrides: Any) -> SendNoticeCommand:
    data: dict[str, Any] = {
        'notice_id': uuid4(),
        'channels': (Channel.EMAIL, Channel.SMS),
        'recipient_uuid': uuid4(),
        'email': EMAIL,
        'cellphone': CELLPHONE,
        'first_name': 'luis',
        'subject': SUBJECT,
        'body': BODY,
    }
    data.update(overrides)
    return SendNoticeCommand(**data)


class _Service:
    """The use case with its fakes, so each test can change one of them."""

    def __init__(self) -> None:
        self.uow = FakeUnitOfWork()
        self.email = FakeChannelSender()
        self.sms = FakeChannelSender()
        self.use_case = SendNoticeUseCase(
            uow=self.uow,
            senders={Channel.EMAIL: self.email, Channel.SMS: self.sms},
            clock=FakeClock(NOW),
        )

    def stored(self, command: SendNoticeCommand, channel: Channel) -> Notification:
        """The committed record of the command's notice for that channel."""
        return self.uow.notifications.stored(command.notice_id, channel)


@pytest.fixture
def service() -> _Service:
    return _Service()


class TestSendNoticeDelivery:
    async def test_sends_every_channel_and_records_each_as_sent(
        self, service: _Service
    ) -> None:
        command = _command()

        await service.use_case.execute(command)

        email = service.stored(command, Channel.EMAIL)
        sms = service.stored(command, Channel.SMS)
        assert (email.status, email.destination) == (NotificationStatus.SENT, EMAIL)
        assert (sms.status, sms.destination) == (NotificationStatus.SENT, CELLPHONE)
        assert email.user_uuid == sms.user_uuid == command.recipient_uuid
        assert email.subject == sms.subject == SUBJECT
        assert email.created_at == sms.created_at == NOW
        assert len(service.email.sent) == len(service.sms.sent) == 1

    async def test_a_notice_only_for_sms_does_not_use_email(
        self, service: _Service
    ) -> None:
        command = _command(channels=(Channel.SMS,), email=None)

        await service.use_case.execute(command)

        assert service.email.sent == []
        assert len(service.uow.notifications.notifications) == 1
        sms = service.stored(command, Channel.SMS)
        assert sms.status == NotificationStatus.SENT

    async def test_a_repeated_notice_sends_nothing_again(
        self, service: _Service
    ) -> None:
        command = _command()
        await service.use_case.execute(command)

        await service.use_case.execute(command)

        assert len(service.email.sent) == len(service.sms.sent) == 1
        assert len(service.uow.notifications.notifications) == 2

    async def test_a_retry_only_resends_the_channel_that_failed(
        self, service: _Service
    ) -> None:
        command = _command()
        service.email.fail_with = DeliveryUnavailableError('timeout')
        with pytest.raises(DeliveryUnavailableError):
            await service.use_case.execute(command)
        service.email.fail_with = None

        await service.use_case.execute(command)

        email = service.stored(command, Channel.EMAIL)
        assert (email.status, email.attempts) == (NotificationStatus.SENT, 2)
        assert len(service.email.sent) == len(service.sms.sent) == 1

    async def test_a_rejected_address_is_recorded_as_failed_without_retry(
        self, service: _Service
    ) -> None:
        command = _command()
        service.email.fail_with = DeliveryRejectedError('address not verified')

        await service.use_case.execute(command)

        email = service.stored(command, Channel.EMAIL)
        sms = service.stored(command, Channel.SMS)
        assert email.status == NotificationStatus.FAILED
        assert sms.status == NotificationStatus.SENT

    async def test_a_temporary_failure_is_committed_as_failed_before_raising(
        self, service: _Service
    ) -> None:
        command = _command()
        service.email.fail_with = DeliveryUnavailableError('timeout')

        with pytest.raises(DeliveryUnavailableError):
            await service.use_case.execute(command)

        email = service.stored(command, Channel.EMAIL)
        assert (email.status, email.attempts) == (NotificationStatus.FAILED, 1)

    async def test_a_temporary_failure_does_not_stop_the_other_channel(
        self, service: _Service
    ) -> None:
        command = _command()
        service.email.fail_with = DeliveryUnavailableError('timeout')

        with pytest.raises(DeliveryUnavailableError):
            await service.use_case.execute(command)

        sms = service.stored(command, Channel.SMS)
        assert sms.status == NotificationStatus.SENT
        assert len(service.sms.sent) == 1

    async def test_stores_the_email_in_lowercase_and_the_subject_trimmed(
        self, service: _Service
    ) -> None:
        command = _command(email='Luis.H@Gmail.com', subject=f'  {SUBJECT}  ')

        await service.use_case.execute(command)

        email = service.stored(command, Channel.EMAIL)
        assert (email.destination, email.subject) == (EMAIL, SUBJECT)

    async def test_logs_each_delivery_with_masked_contacts(
        self, service: _Service, caplog: pytest.LogCaptureFixture
    ) -> None:
        command = _command()
        caplog.set_level(logging.INFO)

        await service.use_case.execute(command)

        assert str(command.notice_id) in caplog.text
        assert SUBJECT in caplog.text
        assert BODY in caplog.text
        assert EMAIL not in caplog.text
        assert CELLPHONE not in caplog.text


class TestSendNoticeRules:
    @pytest.mark.parametrize(
        ('overrides', 'rule'),
        [
            ({'channels': ()}, 'channels must have between 1 and 2'),
            ({'email': None}, 'email is required'),
            ({'email': 'luis.h-gmail.com'}, 'email is invalid'),
            ({'email': 'a@b.c'}, 'email must have between 6 and 254'),
            ({'email': f'{"a" * 245}@gmail.com'}, 'email must have between 6 and 254'),
            ({'cellphone': None}, 'cellphone is required'),
            ({'cellphone': '+51887654321'}, 'cellphone is invalid'),
            ({'cellphone': '+5198765432'}, 'cellphone is invalid'),
            ({'first_name': ''}, 'first_name must have between 1 and 250'),
            ({'first_name': 'a' * 251}, 'first_name must have between 1 and 250'),
            ({'subject': '   '}, 'subject must have between 1 and 250'),
            ({'subject': 'a' * 251}, 'subject must have between 1 and 250'),
            ({'body': ''}, 'body must have between 1 and 4000'),
            ({'body': 'a' * 4001}, 'body must have between 1 and 4000'),
        ],
    )
    async def test_rejects_a_malformed_notice_without_sending_or_recording(
        self, service: _Service, overrides: dict[str, Any], rule: str
    ) -> None:
        with pytest.raises(InvalidNoticeError, match=rule):
            await service.use_case.execute(_command(**overrides))

        assert service.uow.notifications.notifications == []
        assert service.email.sent == service.sms.sent == []

    async def test_reports_every_failing_field_at_once(self, service: _Service) -> None:
        with pytest.raises(InvalidNoticeError) as raised:
            await service.use_case.execute(
                _command(email='luis.h-gmail.com', cellphone='+51887654321')
            )

        assert raised.value.errors == ('email is invalid.', 'cellphone is invalid.')
