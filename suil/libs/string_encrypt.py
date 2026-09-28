import base64

from suil.errors import SecretError


def string_encrypt(plain: str, recipient: str | None) -> str:
    if not recipient:
        raise SecretError('SUIL_AGE_RECIPIENT is not set, nothing to encrypt to')

    try:
        import pyrage
    except ImportError as error:
        raise SecretError('pyrage is not installed - pip install -r requirements.txt') from error

    try:
        target = pyrage.x25519.Recipient.from_str(recipient)
        cipher = pyrage.encrypt(plain.encode(), [target])
    except Exception as error:
        raise SecretError(f'cannot encrypt to {recipient}: {error}') from error

    return base64.b64encode(cipher).decode()
