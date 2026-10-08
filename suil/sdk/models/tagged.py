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
