from datetime import datetime, timezone
from pathlib import Path

import yaml

from pyinfra.facts.server import OsRelease

from suil.errors import NodeProbeError

# os-release ID and ID_LIKE to the family that names a directory under data/os/.
FAMILIES = {
    'rocky':     'redhat',
    'rhel':      'redhat',
    'centos':    'redhat',
    'almalinux': 'redhat',
    'fedora':    'redhat',
    'ubuntu':    'debian',
    'debian':    'debian',
}


def probe_os(host, facts_dir: Path) -> dict:
    """Ask the host what it is. This is the one hierarchy layer whose variables
    are not in the data, so it has to be read before the catalogue is built."""
    release = host.get_fact(OsRelease) or {}
    names = [release.get('id', '')] + (release.get('id_like', '') or '').split()
    family = next((FAMILIES[name] for name in names if name in FAMILIES), None)

    if not family:
        raise NodeProbeError(
            f'{host.name}: /etc/os-release says id={release.get("id")!r} '
            f'id_like={release.get("id_like")!r}, which maps to no data/os/ family')

    version = (release.get('version_id') or '').split('.')[0]

    if not version.isdigit():
        raise NodeProbeError(f'{host.name}: VERSION_ID is {release.get("version_id")!r}, no major version in it')

    probe = {'family': family, 'release': int(version), 'id': release.get('id')}

    target = Path(facts_dir) / host.name
    target.mkdir(parents=True, exist_ok=True)
    (target / 'suil.yaml').write_text(yaml.safe_dump(
        {'facts': probe, 'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')},
        default_flow_style=False, sort_keys=False))

    return probe
