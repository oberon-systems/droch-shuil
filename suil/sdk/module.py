from typing import Generic, TypeVar

from .libs import module as libs
from .models import Config

ConfigT = TypeVar('ConfigT', bound=Config)


class Module(Generic[ConfigT]):
    """Base of every module's code/main.py.

    deploy() and expected() are mandatory, check() and files() optional, and
    the libs are there for the module to use or not.
    """

    def __init__(self, config: ConfigT) -> None:
        self.config = config

        for name in libs.__all__:
            setattr(self, name, getattr(libs, name))

    def deploy(self, facts: dict, force: bool) -> None:
        """Queue the operations that close the diff."""
        raise NotImplementedError

    def expected(self) -> dict:
        """The state the facts must match."""
        raise NotImplementedError

    def check(self, facts: dict) -> list[str]:
        """Problems judged from the facts."""
        return []

    def files(self) -> dict[str, str | bytes | None]:
        """Path to content of every file the module puts on the node, None for one that must go."""
        return {}
