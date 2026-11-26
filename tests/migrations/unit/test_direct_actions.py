import pytest

from app.migrations.direct_actions import handle_direct_action, is_direct_action
from tests.fakes.migrations import FakeMigrator


class TestIsDirectAction:
    def test_an_event_with_an_action_is_direct(self) -> None:
        assert is_direct_action({'action': 'current'})

    def test_a_cloudformation_event_is_not_direct(self) -> None:
        assert not is_direct_action({'RequestType': 'Update'})


class TestHandleDirectAction:
    def test_current_returns_the_revision(self) -> None:
        migrator = FakeMigrator(revision='abc123')

        assert handle_direct_action({'action': 'current'}, migrator) == {
            'revision': 'abc123'
        }

    def test_current_returns_none_at_base(self) -> None:
        assert handle_direct_action({'action': 'current'}, FakeMigrator()) == {
            'revision': None
        }

    def test_downgrade_undoes_to_the_revision_and_returns_it(self) -> None:
        migrator = FakeMigrator(revision='def456')

        reply = handle_direct_action(
            {'action': 'downgrade', 'revision': 'abc123'}, migrator
        )

        assert migrator.downgraded_to == ['abc123']
        assert reply == {'revision': 'abc123'}

    @pytest.mark.parametrize(
        'event', [{'action': 'downgrade'}, {'action': 'downgrade', 'revision': ''}]
    )
    def test_downgrade_without_a_revision_fails(self, event: dict[str, object]) -> None:
        migrator = FakeMigrator(revision='def456')

        with pytest.raises(ValueError, match='downgrade needs a revision'):
            handle_direct_action(event, migrator)
        assert migrator.downgraded_to == []

    def test_an_unknown_action_fails(self) -> None:
        with pytest.raises(ValueError, match='Unknown action: drop'):
            handle_direct_action({'action': 'drop'}, FakeMigrator())
