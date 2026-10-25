"""Offline guardrail.

The factory intentionally has no provider adapter: it does not call APIs or AI.
Keeping this module makes the no-network contract explicit for coding tools.
"""
from __future__ import annotations


class OfflineOnlyError(RuntimeError):
    pass


class OfflineProvider:
    """Fails closed if a future edit attempts external model or HTTP use."""

    def complete(self, *_args: object, **_kwargs: object) -> str:
        raise OfflineOnlyError("Factory is offline-only: provider calls and network access are disabled.")
