import hashlib


def file_digest(content: str | bytes | None) -> str | None:
    """The sha256 a file with this content has on the target. None is no file."""
    if content is None:
        return None

    return hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest()
