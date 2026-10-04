"""Types shared by the runner and by every module's config.py."""

from pydantic import BaseModel, ConfigDict

from suil.errors import DataError
from suil.sdk.models import Encrypted as Secret

__all__ = ['Secret', 'Tagged', 'Lookup', 'SuilContext', 'SuilConfig']


class Tagged:
    """A value carrying a merge strategy tag - !append, !replace, !merge, !delete."""

    __slots__ = ('strategy', 'value')

    STRATEGIES = ('append', 'replace', 'merge', 'delete')

    def __init__(self, strategy: str, value):
        self.strategy = strategy
        self.value = value

    def __repr__(self) -> str:
        return f'Tagged({self.strategy!r}, {self.value!r})'

    def __eq__(self, other) -> bool:
        return (isinstance(other, Tagged)
                and other.strategy == self.strategy
                and other.value == self.value)


class Lookup:
    """A !LOOKUP marker: a query over the inventory, standing in for data that
    belongs to other nodes.

    It survives the merge untouched and is expanded once, against the whole
    directory, after the last layer has been folded in.
    """

    __slots__ = ('nodes', 'role', 'field', 'ip', 'format', 'scope')

    KEYS = ('nodes', 'role', 'field', 'ip', 'format', 'self')
    IP_KINDS = ('v4', 'v6', 'any')
    SCOPES = ('include', 'exclude', 'only')

    def __init__(self, spec: dict):
        if not isinstance(spec, dict):
            raise DataError(f'!LOOKUP takes a mapping of {", ".join(self.KEYS)}, got {spec!r}')

        if unknown := sorted(set(spec) - set(self.KEYS)):
            raise DataError(f'!LOOKUP does not know {", ".join(unknown)}; '
                            f'it takes {", ".join(self.KEYS)}')

        if not spec.get('field'):
            raise DataError('!LOOKUP needs a field: the dotted path it reads on every node')

        self.nodes = spec.get('nodes') or '*'
        self.role = spec.get('role')
        self.field = spec['field']
        self.ip = spec.get('ip') or 'any'
        self.format = spec.get('format') or '{value}'
        self.scope = spec.get('self') or 'include'

        if self.ip not in self.IP_KINDS:
            raise DataError(f'!LOOKUP ip is one of {", ".join(self.IP_KINDS)}, not {self.ip!r}')

        if self.scope not in self.SCOPES:
            raise DataError(f'!LOOKUP self is one of {", ".join(self.SCOPES)}, not {self.scope!r}')

    def __repr__(self) -> str:
        return f'Lookup({self.field!r}, nodes={self.nodes!r}, format={self.format!r})'

    def __eq__(self, other) -> bool:
        return (isinstance(other, Lookup)
                and all(getattr(other, name) == getattr(self, name) for name in self.__slots__))


class SuilContext(BaseModel):
    """Node identity, injected into every module config by the runner."""

    model_config = ConfigDict(extra='forbid')

    node:     str
    role:     str | None = None
    family:   str
    release:  int
    ssh_user: str | None = None


class SuilConfig(BaseModel):
    """Base of every module's Config. A key the model does not know is an error."""

    model_config = ConfigDict(extra='forbid')

    suil: SuilContext
