"""Every function of an interface, as the loader checks it."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Deploys(Protocol):

    def deploy(self, facts: dict, force: bool) -> None: ...


@runtime_checkable
class Expects(Protocol):

    def expected(self) -> dict: ...


@runtime_checkable
class Checks(Protocol):

    def check(self, facts: dict) -> list[str]: ...


@runtime_checkable
class DeclaresFiles(Protocol):

    def files(self) -> dict[str, str | bytes | None]: ...


@runtime_checkable
class Collects(Protocol):

    def collect(self) -> dict: ...
