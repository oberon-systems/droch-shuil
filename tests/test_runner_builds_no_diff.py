import re

from pathlib import Path

import suil

RUNNER_DIFF = re.compile(r'\bdiff\b|diff_configs')
RUNNER = ('deployment.py', 'sdk/libs/module/run_code.py')


def test_the_runner_neither_builds_nor_passes_a_diff():
    root = Path(suil.__file__).parent

    assert [name for name in RUNNER if RUNNER_DIFF.search((root / name).read_text())] == []
