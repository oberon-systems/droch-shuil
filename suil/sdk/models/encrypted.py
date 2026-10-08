import hashlib


class Encrypted(str):
    """A value that arrived through an !ENC marker.

    The str value is the ciphertext, so a stray dump writes the ciphertext back
    rather than the plaintext; reveal() decrypts on demand.
    """

    __slots__ = ('_plain',)

    def reveal(self, key: str | None = None) -> str:
        plain = getattr(self, '_plain', None)

        if plain is None:
            from suil.sdk.libs.string.decrypt import decrypt

            plain = decrypt(str(self), key)
            object.__setattr__(self, '_plain', plain)

        return plain

    def digest(self) -> str:
        return 'sha256:' + hashlib.sha256(self.reveal().encode()).hexdigest()
