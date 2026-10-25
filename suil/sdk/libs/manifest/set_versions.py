import re

import yaml

from suil.sdk.errors import ManifestError
from suil.sdk.models.repo import LOCAL

REPO = re.compile(r'^\s*-\s*repo:\s*(\S+)')
PIN = re.compile(r'^(\s+)([^\s:#\'"]+)(:\s*)(\S+)(.*)$')


def set_versions(text: str, versions: dict[str, str]) -> str:
    """modules.yaml with the version of each module in `versions` replaced, line by line,
    so the layout and the comments stay as they were."""
    lines, local = [], True

    for line in text.splitlines(keepends=True):
        body = line.rstrip('\n')

        if found := REPO.match(body):
            local = found.group(1).strip('\'"') == LOCAL
        elif not local and (found := PIN.match(body)) and found.group(2) in versions:
            version = versions[found.group(2)]
            value = version if yaml.safe_load(version) == version else f"'{version}'"
            line = f'{found.group(1)}{found.group(2)}{found.group(3)}{value}{found.group(5)}' + line[len(body):]

        lines.append(line)

    result = ''.join(lines)
    written = {name: version for entry in (yaml.safe_load(result) or {}).get('repos', [])
               if isinstance(entry.get('modules'), dict) for name, version in entry['modules'].items()}

    if missed := sorted(name for name, version in versions.items() if written.get(name) != version):
        raise ManifestError(f"modules.yaml: cannot rewrite the version of {', '.join(missed)}; set it by hand")

    return result
