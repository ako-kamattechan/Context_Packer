from __future__ import annotations
from dataclasses import dataclass
from .errors import ContextPackerError


class CancelledError(ContextPackerError):
    pass


@dataclass
class CancelToken:
    requested: bool = False

    def check(self) -> None:
        if self.requested:
            raise CancelledError("Operation cancelled by user.")


def check_cancel(token: CancelToken | None) -> None:
    if token:
        token.check()
