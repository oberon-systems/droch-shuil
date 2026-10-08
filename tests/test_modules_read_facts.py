import re

from pathlib import Path

import suil

HOST_READS = re.compile(r'\b(get_fact|host_run_command|run_command)\b')
RUNNER_DIFF = re.compile(r'\bdiff\b|diff_configs')
RUNNER = ('deployment.py', 'sdk/libs/module/run_code.py')


def test_no_module_reads_the_host_outside_its_collector(modules_dir):
    offenders = [f'{path.relative_to(modules_dir)}:{number}'
                 for path in sorted(Path(modules_dir).glob('*/code/*.py'))
                 for number, line in enumerate(path.read_text().splitlines(), 1)
                 if HOST_READS.search(line)]

    assert offenders == []


def test_the_runner_neither_builds_nor_passes_a_diff():
    root = Path(suil.__file__).parent

    assert [name for name in RUNNER if RUNNER_DIFF.search((root / name).read_text())] == []
