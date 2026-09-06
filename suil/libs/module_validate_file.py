import shlex

from suil.errors import ModuleValidateError

from .host_put_content import host_put_content
from .host_run_command import host_run_command


def module_validate_file(host, content: str, checker: str) -> str:
    """Stage a rendered file on the target and let the target's own checker judge it.

    `checker` carries %s where the path goes - 'sshd -t -f %s', 'nft -c -f %s'.
    Both halves are connector calls, so this finishes before any operation runs
    and a rejected file never reaches its destination.
    """
    staged = host.get_temp_filename(content)

    if not host_put_content(host, content, staged):
        raise ModuleValidateError(f'cannot stage a file at {staged} on {host.name}')

    command = checker.replace('%s', shlex.quote(staged))
    status, stdout, stderr = host_run_command(host, command)
    host_run_command(host, f'rm -f {shlex.quote(staged)}')

    if not status:
        message = (stderr or stdout or '').strip()
        raise ModuleValidateError(f'{host.name}: `{checker}` rejected the rendered file\n{message}')

    return staged
