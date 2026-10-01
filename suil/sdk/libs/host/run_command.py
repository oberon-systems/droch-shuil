from pyinfra.api import StringCommand

from .sudo_password import sudo_password


def run_command(host, command: str, sudo: bool = True) -> tuple[bool, str, str]:
    """One shell command on a connected host, outside any operation.
    """
    status, output = host.run_shell_command(StringCommand(command), _sudo=sudo,
                                            _sudo_password=sudo_password(host))

    return bool(status), output.stdout, output.stderr
