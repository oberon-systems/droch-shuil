from io import StringIO

from .sudo_password import sudo_password


def put_content(host, content: str, remote_path: str, sudo: bool = True) -> bool:
    """Upload a string to the host outside any operation, for a check that has
    to happen before the file is declared into place."""
    return bool(host.put_file(StringIO(content), remote_path, _sudo=sudo,
                              _sudo_password=sudo_password(host)))
