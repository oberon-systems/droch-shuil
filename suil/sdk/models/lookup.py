from suil.sdk.errors import DataError


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
