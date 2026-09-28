from pathlib import Path

from suil.errors import ModuleConfigError

from .config_strip_secrets import config_reveal_secrets
from .module_load_code import module_load_code


def module_get_config(module: str, node, modules_dir: Path, age_key: str | None):
    """The module's slice of the node config, validated by its own pydantic model.

    Returns the model instance when the module ships code/config.py, and the
    plain dict when it does not - a meta module has nothing to validate.
    """
    data = dict(getattr(node, module, None) or {})
    data['suil'] = {
        'node':     node.name,
        'role':     node.role,
        'family':   node.family,
        'release':  node.release,
        'ssh_user': (node.deployment or {}).get('ssh_user'),
    }

    data = config_reveal_secrets(data, age_key)
    code = module_load_code(module, modules_dir, part='config')

    if code is None:
        return data

    model = getattr(code, 'Config', None)

    if model is None:
        raise ModuleConfigError(f'modules/{module}/code/config.py declares no Config')

    try:
        return model(**data)
    except Exception as error:
        raise ModuleConfigError(f'{module} config for {node.name} is not valid:\n{error}') from error
