import re

from pathlib import Path

HOST_READS = re.compile(r'\b(get_fact|host_run_command)\b')
RUNNER_DIFF = re.compile(r'\bdiff\b|module_diff_configs')
RUNNER = ('deployment.py', 'libs/module_run_code.py')


def test_no_module_reads_the_host_outside_its_collector(modules_dir):
    offenders = [f'{path.relative_to(modules_dir)}:{number}'
                 for path in sorted(Path(modules_dir).glob('*/code/*.py'))
                 for number, line in enumerate(path.read_text().splitlines(), 1)
                 if HOST_READS.search(line)]

    assert offenders == []


def test_the_runner_neither_builds_nor_passes_a_diff():
    root = Path(__file__).resolve().parent.parent

    assert [name for name in RUNNER if RUNNER_DIFF.search((root / name).read_text())] == []
