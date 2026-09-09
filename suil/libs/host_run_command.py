from pyinfra.api import StringCommand

from .host_sudo_password import host_sudo_password


def host_run_command(host, command: str, sudo: bool = True) -> tuple[bool, str, str]:
    """One shell command on a connected host, outside any operation.
    """
    status, output = host.run_shell_command(StringCommand(command), _sudo=sudo,
                                            _sudo_password=host_sudo_password(host))

    return bool(status), output.stdout, output.stderr
