from typing import Protocol

# Invoked directly by the deploy, not by CloudFormation: record the revision before
# deploying and undo the migrations when the deploy fails.


class RevisionMigrator(Protocol):
    def current(self) -> str | None: ...

    def downgrade(self, revision: str) -> str | None: ...


def is_direct_action(event: dict[str, object]) -> bool:
    return 'action' in event


def handle_direct_action(
    event: dict[str, object], migrator: RevisionMigrator
) -> dict[str, str | None]:
    """{"action": "current"} -> {"revision": <rev or None>};
    {"action": "downgrade", "revision": "<rev>"} -> {"revision": <rev reached>}.
    Anything else raises: the Lambda replies with a FunctionError."""
    action = event.get('action')
    if action == 'current':
        return {'revision': migrator.current()}
    if action == 'downgrade':
        revision = event.get('revision')
        if not isinstance(revision, str) or not revision:
            raise ValueError('downgrade needs a revision')
        return {'revision': migrator.downgrade(revision)}
    raise ValueError(f'Unknown action: {action}')
