import base64
import re

from suil.errors import SecretError

# The marker as it survives both YAML forms: the tag name and the folded string.
MARKER = re.compile(r'^\s*!ENC\[\s*(?P<payload>[A-Za-z0-9+/=\s]+?)\s*\]\s*$')


def decrypt(cipher: str, key: str | None) -> str:
    if not key:
        raise SecretError('SUIL_AGE_KEY is not set, an encrypted value cannot be read')

    if match := MARKER.match(cipher):
        cipher = match.group('payload')

    try:
        import pyrage
    except ImportError as error:
        raise SecretError('pyrage is not installed - pip install -r requirements.txt') from error

    try:
        identity = pyrage.x25519.Identity.from_str(key)
        plain = pyrage.decrypt(base64.b64decode(''.join(cipher.split())), [identity])
    except Exception as error:
        raise SecretError(f'cannot decrypt the value: {error}') from error

    return plain.decode()
