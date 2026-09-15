import json
import shlex

from suil.errors import ModuleError

from .host_run_command import host_run_command

SCRIPT = '''
import hashlib, json, sys

def digest(path):
    try:
        with open(path, "rb") as stream:
            return hashlib.sha256(stream.read()).hexdigest()
    except OSError:
        return None

print(json.dumps({path: digest(path) for path in json.loads(sys.argv[1])}))
'''


def module_collect_files(host, paths) -> dict[str, str | None]:
    """The sha256 of every path on the target, None where there is no such file."""
    paths = sorted(set(paths))

    if not paths:
        return {}

    status, stdout, stderr = host_run_command(
        host, f'python3 -c {shlex.quote(SCRIPT)} {shlex.quote(json.dumps(paths))}')

    if not status:
        raise ModuleError(f'{host.name}: file digests not read\n{(stderr or stdout).strip()}')

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ModuleError(f'{host.name}: file digests printed no JSON: {error}') from error
