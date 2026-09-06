import json
import shlex

from datetime import datetime, timezone
from pathlib import Path

import yaml

from suil.errors import ModuleError

from .config_strip_secrets import config_strip_secrets
from .host_put_content import host_put_content
from .host_run_command import host_run_command
from .module_get_signature import module_get_signature


def module_collect_facts(host, module: str, config, modules_dir: Path, facts_dir: Path) -> dict:
    """Run the module's collector on the target and record what it reports.

    The collector is handed the config with the secrets already replaced by
    their digests: it needs to know which resources to describe, not their
    values.
    """
    collector = Path(modules_dir) / module / 'facts' / 'collector.py'

    if not collector.is_file():
        return {}

    payload = config if isinstance(config, dict) else config.model_dump(mode='json', exclude={'suil'})
    payload = config_strip_secrets(payload)

    remote_code = host.get_temp_filename(f'{module}-collector')
    remote_conf = host.get_temp_filename(f'{module}-config')

    if not host_put_content(host, collector.read_text(), remote_code):
        raise ModuleError(f'cannot upload the {module} collector to {host.name}')

    if not host_put_content(host, json.dumps(payload), remote_conf):
        raise ModuleError(f'cannot upload the {module} config to {host.name}')

    status, stdout, stderr = host_run_command(
        host, f'python3 {shlex.quote(remote_code)} {shlex.quote(remote_conf)}')
    host_run_command(host, f'rm -f {shlex.quote(remote_code)} {shlex.quote(remote_conf)}')

    if not status:
        raise ModuleError(f'{host.name}: the {module} collector failed\n{(stderr or stdout).strip()}')

    try:
        facts = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ModuleError(f'{host.name}: the {module} collector printed no JSON: {error}') from error

    record = {
        'facts':     facts,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'signature': module_get_signature(module, modules_dir),
    }

    target = Path(facts_dir) / host.name
    target.mkdir(parents=True, exist_ok=True)
    (target / f'{module}.yaml').write_text(
        yaml.safe_dump(record, default_flow_style=False, sort_keys=False))

    return record
