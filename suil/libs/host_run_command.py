from pyinfra.api import StringCommand


def host_run_command(host, command: str, sudo: bool = True) -> tuple[bool, str, str]:
    """One shell command on a connected host, outside any operation.
    """
    status, output = host.run_shell_command(StringCommand(command), _sudo=sudo)

    return bool(status), output.stdout, output.stderr
