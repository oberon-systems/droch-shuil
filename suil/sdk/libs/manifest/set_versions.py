import re

import yaml

from suil.sdk.errors import ManifestError

REPO = re.compile(r'^\s*-\s*repo:\s*(\S+)')
VERSION = re.compile(r'^(\s*version:\s*)\S+(.*)$')


def set_versions(text: str, versions: dict[str, str]) -> str:
    """modules.yaml with the version of each repository in `versions` replaced, line by line,
    so the layout and the comments stay as they were."""
    lines, current = [], None

    for line in text.splitlines(keepends=True):
        if found := REPO.match(line):
            current = found.group(1).strip('\'"')
        elif current in versions and (found := VERSION.match(line.rstrip('\n'))):
            version = versions[current]
            value = version if yaml.safe_load(version) == version else f"'{version}'"
            line = f'{found.group(1)}{value}{found.group(2)}' + line[len(line.rstrip('\n')):]

        lines.append(line)

    result = ''.join(lines)
    written = {entry['repo']: entry.get('version') for entry in (yaml.safe_load(result) or {}).get('repos', [])}

    if missed := sorted(url for url, version in versions.items() if written.get(url) != version):
        raise ManifestError(f"modules.yaml: cannot rewrite the version of {', '.join(missed)}; set it by hand")

    return result
