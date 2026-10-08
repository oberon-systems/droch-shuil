import re

from suil.sdk.errors import ModuleError
from suil.sdk.models import Root

HOST_READS = re.compile(r'\b(get_fact|host_run_command|run_command)\b')


def check_host_reads(root: Root) -> None:
    """Only facts/collector.py reads a node; the code under code/ works from the facts it is given."""
    for path in sorted((root.path / 'code').glob('*.py')):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if found := HOST_READS.search(line):
                raise ModuleError(f'modules/{root.name}/code/{path.name}:{number} calls {found.group(1)}; '
                                  f'read the node in facts/collector.py and take it from the facts')
