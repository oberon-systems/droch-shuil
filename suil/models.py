"""Types shared by the runner and by every module's config.py."""

import hashlib

from pydantic import BaseModel, ConfigDict


class Secret(str):
    """A value that arrived through an !ENC marker.

    The str value is the ciphertext, so a stray dump writes the ciphertext back
    rather than the plaintext; reveal() decrypts on demand.
    """

    __slots__ = ('_plain',)

    def reveal(self) -> str:
        plain = getattr(self, '_plain', None)

        if plain is None:
            from suil.libs.string_decrypt import string_decrypt

            plain = string_decrypt(str(self))
            object.__setattr__(self, '_plain', plain)

        return plain

    def digest(self) -> str:
        return 'sha256:' + hashlib.sha256(self.reveal().encode()).hexdigest()


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
