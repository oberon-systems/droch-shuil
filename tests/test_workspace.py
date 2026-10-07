import os
import subprocess
import sys

import pytest

from suil.directory import Directory
from suil.errors import DirectoryError
from suil.sdk.errors import DataError
from suil.workspace import Workspace

COMMON = 'hierarchy:\n  - roles/{role}.yaml\n  - nodes/{node}.yaml\n'


def tree(root, node, value):
    for path, text in {
        'data/common.yaml':                COMMON,
        'data/roles/web.yaml':             'modules:\n  - demo\n',
        f'data/nodes/{node}.yaml':         f'role: web\ndemo:\n  value: {value}\n',
        'modules/demo/requires.yaml':      'requires: []\n',
        'modules.yaml':                    'repos:\n  - repo: local\n    modules: [demo]\n',
    }.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)

    return Workspace(root)


def test_importing_suil_reads_no_environment(tmp_path):
    (tmp_path / '.env').write_text('SUIL_PROBE=1\n')
    script = "import os, suil.cli; assert 'SUIL_PROBE' not in os.environ"
    env = {**os.environ, 'SUIL_LOG_COLOR': 'not-a-bool'}

    assert subprocess.run([sys.executable, '-c', script], cwd=tmp_path, env=env).returncode == 0


def test_two_workspaces_build_their_runs_in_one_process(tmp_path):
    one = Directory(tree(tmp_path / 'one', 'a-01.example.com', 'a'), role='web')
    two = Directory(tree(tmp_path / 'two', 'b-01.example.com', 'b'), role='web')

    assert [(node.name, node.demo['value']) for node in one.nodes] == [('a-01.example.com', 'a')]
    assert [(node.name, node.demo['value']) for node in two.nodes] == [('b-01.example.com', 'b')]


def test_a_role_or_a_node_that_is_not_there_fails(tmp_path):
    workspace = tree(tmp_path, 'a-01.example.com', 'a')

    with pytest.raises(DataError):
        Directory(workspace, role='nowhere')

    with pytest.raises(DataError):
        Directory(workspace, node='nowhere.example.com')


def test_a_run_is_a_role_or_a_node_and_never_changes(tmp_path):
    workspace = tree(tmp_path, 'a-01.example.com', 'a')
    directory = Directory(workspace, node='a-01.example.com')

    with pytest.raises(DirectoryError):
        Directory(workspace, role='web', node='a-01.example.com')

    with pytest.raises(AttributeError):
        directory.nodes = ()

    directory.nodes[0].demo['value'] = 'changed'

    assert directory.nodes[0].demo['value'] == 'a'
