import json
import subprocess
import sys

import pytest

from suil.sdk import facter
from suil.sdk.errors import ModuleError
from suil.sdk.libs.module import check_facter
from suil.sdk.models import Root, Secret

HEAD = 'import os\n\nfrom suil.sdk import Facter\n\n\n'

DEMO = HEAD + '''class Demo(Facter):

    def collect(self) -> dict:
        return {'config': self.config, 'digest': self.digest('pw'), 'cwd': bool(os.getcwd())}
'''


def collector(tmp_path, name, source):
    facts = tmp_path / name / 'facts'
    facts.mkdir(parents=True)
    (facts / 'collector.py').write_text(source)

    return Root(name=name, path=tmp_path / name)


def test_a_good_collector_and_a_module_without_one_pass(tmp_path):
    check_facter(collector(tmp_path, 'facter_demo', DEMO))
    check_facter(Root(name='facter_absent', path=tmp_path / 'facter_absent'))


@pytest.mark.parametrize('source, error', [
    ('import yaml\n' + DEMO, 'imports yaml'),
    (HEAD, 'found: none'),
    (DEMO + '\n\nclass More(Facter):\n    pass\n', 'found: Demo, More'),
    (HEAD + 'class Demo(Facter):\n    pass\n', r'does not override collect\(\)'),
    (HEAD + 'class Demo(Facter):\n\n    def collect(self, extra) -> dict:\n        return {}\n', 'must be collect'),
    ('class (\n', 'does not parse'),
])
def test_a_collector_off_the_contract_is_refused(tmp_path, source, error):
    with pytest.raises(ModuleError, match=error):
        check_facter(collector(tmp_path, 'facter_bad', source))


def test_the_bootstrap_prints_what_collect_returns(tmp_path):
    collector(tmp_path, 'facter_run', DEMO)
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'a': 1}))

    result = subprocess.run([sys.executable, facter.__file__, str(tmp_path / 'facter_run' / 'facts' / 'collector.py'),
                             str(config)], capture_output=True, text=True, check=True)

    assert json.loads(result.stdout) == {'config': {'a': 1}, 'digest': Secret('pw').digest(), 'cwd': True}


def test_the_bootstrap_refuses_two_facters(tmp_path):
    collector(tmp_path, 'facter_two', DEMO + '\n\nclass More(Facter):\n    pass\n')
    config = tmp_path / 'config.json'
    config.write_text('{}')

    result = subprocess.run([sys.executable, facter.__file__, str(tmp_path / 'facter_two' / 'facts' / 'collector.py'),
                             str(config)], capture_output=True, text=True)

    assert result.returncode != 0
    assert 'exactly one Facter subclass, found 2' in result.stderr
