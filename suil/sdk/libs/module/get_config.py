from pathlib import Path

from suil.sdk.errors import ModuleConfigError
from suil.sdk.models import Secret

from ..config.strip_secrets import reveal_secrets, strip_secrets
from .load_code import load_code


def get_config(module: str, node, modules_dir: Path, age_key: str | None):
    """The module's slice of the node config, validated by its own pydantic model.

    Returns the model instance when the module ships code/config.py, and the
    plain dict when it does not - a meta module has nothing to validate.
    Every !ENC value reaches the model as a Secret, and has to stay one.
    """
    data = dict(getattr(node, module, None) or {})
    data['suil'] = {
        'node':     node.name,
        'role':     node.role,
        'family':   node.family,
        'release':  node.release,
        'ssh_user': (node.deployment or {}).get('ssh_user'),
    }

    data = reveal_secrets(data, age_key)
    code = load_code(module, modules_dir, part='config')

    if code is None:
        return data

    model = getattr(code, 'Config', None)

    if model is None:
        raise ModuleConfigError(f'modules/{module}/code/config.py declares no Config')

    try:
        config = model(**data)
    except Exception as error:
        raise ModuleConfigError(f'{module} config for {node.name} is not valid:\n{error}') from error

    secrets = set(_secrets(data))

    if leak := next(_leaks(strip_secrets(config), secrets, module), None):
        raise ModuleConfigError(f'{module} config for {node.name}: {leak} holds an !ENC value, '
                                f'but its field is not typed Secret')

    return config


def _secrets(data):
    if isinstance(data, Secret) and data:
        yield str(data)

    elif isinstance(data, dict):
        for value in data.values():
            yield from _secrets(value)

    elif isinstance(data, list):
        for value in data:
            yield from _secrets(value)


def _leaks(data, secrets: set, path: str):
    if isinstance(data, str) and data in secrets:
        yield path

    elif isinstance(data, dict):
        for key, value in data.items():
            yield from _leaks(value, secrets, f'{path}.{key}')

    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from _leaks(value, secrets, f'{path}[{index}]')
