import json
import shlex

from datetime import datetime, timezone
from pathlib import Path

import yaml

from suil.errors import ModuleError

from ...protocols import DeclaresFiles
from ..host.put_content import put_content
from ..host.run_command import run_command
from .collect_files import collect_files
from .get_files import get_files
from .get_signature import get_signature


def collect_facts(host, module: str, config, instance: DeclaresFiles | None, modules_dir: Path,
                  facts_dir: Path) -> dict:
    """Run the module's collector on the target and record what it reports,
    together with the digest of every file the module puts there.

    `config` is the public view built by get_public - secrets are
    already digests, and it is all the collector ever sees. `instance` renders
    the files and never leaves the control machine.
    """
    collector = Path(modules_dir) / module / 'facts' / 'collector.py'
    files = get_files(instance)

    if not collector.is_file() and not files:
        return {}

    facts = _collector(host, module, config, collector) if collector.is_file() else {}

    if files:
        facts['files'] = collect_files(host, files)

    record = {
        'facts':     facts,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'signature': get_signature(module, modules_dir),
    }

    target = Path(facts_dir) / host.name
    target.mkdir(parents=True, exist_ok=True)
    (target / f'{module}.yaml').write_text(
        yaml.safe_dump(record, default_flow_style=False, sort_keys=False))

    return record


def _collector(host, module: str, config, collector: Path) -> dict:
    payload = {key: value for key, value in config.items() if key != 'suil'}

    remote_code = host.get_temp_filename(f'{module}-collector')
    remote_conf = host.get_temp_filename(f'{module}-config')

    if not put_content(host, collector.read_text(), remote_code):
        raise ModuleError(f'cannot upload the {module} collector to {host.name}')

    if not put_content(host, json.dumps(payload), remote_conf):
        raise ModuleError(f'cannot upload the {module} config to {host.name}')

    status, stdout, stderr = run_command(
        host, f'python3 {shlex.quote(remote_code)} {shlex.quote(remote_conf)}')
    run_command(host, f'rm -f {shlex.quote(remote_code)} {shlex.quote(remote_conf)}')

    if not status:
        raise ModuleError(f'{host.name}: the {module} collector failed\n{(stderr or stdout).strip()}')

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ModuleError(f'{host.name}: the {module} collector printed no JSON: {error}') from error
