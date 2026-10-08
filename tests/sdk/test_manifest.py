import shutil
import subprocess

import pytest

from suil.sdk.errors import ManifestError, ModuleError, ModuleOrderError
from suil.sdk.libs.manifest import (check_manifest, get_checkout, get_latest_tag, install_repo, read_manifest,
                                    set_versions)
from suil.sdk.models import Repo

GIT = ['git', '-c', 'user.name=test', '-c', 'user.email=test@example.com',
       '-c', 'commit.gpgsign=false', '-c', 'tag.gpgsign=false']


def git(path, *args):
    return subprocess.run([*GIT, '-C', str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def remote(tmp_path):
    """Modules one and two, v1.0 a plain tag, v1.1 an annotated one, and a branch edge."""
    path = tmp_path / 'remote'

    for name, requires in {'one': 'two', 'two': ''}.items():
        (path / name).mkdir(parents=True)
        (path / name / 'requires.yaml').write_text(f'requires: [{requires}]\n')

    git(tmp_path, 'init', '-q', '-b', 'main', str(path))
    git(path, 'add', '.')
    git(path, 'commit', '-q', '-m', 'one')
    git(path, 'tag', 'v1.0')
    git(path, 'branch', 'edge')
    git(path, 'commit', '-q', '--allow-empty', '-m', 'two')
    git(path, 'tag', '-a', 'v1.1', '-m', 'v1.1')

    return path


def workspace(tmp_path, text, local=None):
    for name, requires in (local or {}).items():
        (tmp_path / 'modules' / name).mkdir(parents=True)
        (tmp_path / 'modules' / name / 'requires.yaml').write_text(f'requires: [{requires}]\n')

    (tmp_path / 'modules.yaml').write_text(text)

    return tmp_path / 'modules.yaml', tmp_path / 'modules', tmp_path / 'cache'


def entry(remote, version, modules='one, two'):
    return f'  - repo:    {remote}\n    version: {version}\n    modules: [{modules}]\n'


def test_a_tag_installs_cold_and_validates_warm_with_the_remote_gone(tmp_path, remote):
    file, modules, cache = workspace(tmp_path, 'repos:\n' + entry(remote, 'v1.1'))
    repo = read_manifest(file).repos[0]

    with pytest.raises(ManifestError, match='run suil install'):
        check_manifest(file, modules, cache)

    checkout = install_repo(repo, cache)

    assert git(checkout, 'rev-parse', 'HEAD') == git(remote, 'rev-parse', 'v1.1^{commit}')

    shutil.rmtree(remote)

    assert install_repo(repo, cache) is None
    assert {name: root.path for name, root in check_manifest(file, modules, cache).items()} == {
        'one': checkout / 'one', 'two': checkout / 'two'}


def test_a_sha_installs(tmp_path, remote):
    sha = git(remote, 'rev-parse', 'v1.0')
    file, modules, cache = workspace(tmp_path, 'repos:\n' + entry(remote, sha))

    checkout = install_repo(read_manifest(file).repos[0], cache)

    assert git(checkout, 'rev-parse', 'HEAD') == sha
    assert check_manifest(file, modules, cache)['one'].version == sha


def test_a_branch_is_refused_and_leaves_nothing_in_the_cache(tmp_path, remote):
    repo = Repo(repo=str(remote), version='edge', modules=['one'])

    with pytest.raises(ManifestError, match='is a branch'):
        install_repo(repo, tmp_path / 'cache')

    assert list(get_checkout(tmp_path / 'cache', repo.repo, 'edge').parent.iterdir()) == []


def test_a_module_missing_from_its_repository_is_named(tmp_path, remote):
    file, modules, cache = workspace(tmp_path, 'repos:\n' + entry(remote, 'v1.0', 'one, two, three'))
    install_repo(read_manifest(file).repos[0], cache)

    with pytest.raises(ManifestError, match='module three is not in'):
        check_manifest(file, modules, cache)


def test_a_name_declared_twice_is_refused(tmp_path, remote):
    file, _, _ = workspace(tmp_path, 'repos:\n' + entry(remote, 'v1.0') + '  - repo: local\n    modules: [one]\n')

    with pytest.raises(ManifestError, match='declared twice: one'):
        read_manifest(file)


@pytest.mark.parametrize('text', [
    'repos:\n  - repo: https://git.example.com/m\n    modules: [one]\n',
    'repos:\n  - repo: local\n    version: v1\n    modules: [one]\n',
    'repos:\n  - repo: local\n    modules: [one]\n    rev: v1\n',
])
def test_a_git_repo_needs_a_version_and_local_takes_none(tmp_path, text):
    file, _, _ = workspace(tmp_path, text)

    with pytest.raises(ManifestError, match='modules.yaml is not valid'):
        read_manifest(file)


def test_a_requires_cycle_is_refused(tmp_path):
    files = workspace(tmp_path, 'repos:\n  - repo: local\n    modules: [a, b]\n', {'a': 'b', 'b': 'a'})

    with pytest.raises(ModuleOrderError, match='cycle'):
        check_manifest(*files)


def test_a_directory_not_declared_is_refused(tmp_path):
    files = workspace(tmp_path, 'repos:\n  - repo: local\n    modules: [a]\n', {'a': '', 'extra': ''})

    with pytest.raises(ManifestError, match='modules/extra not declared'):
        check_manifest(*files)


def test_a_meta_module_holds_its_requires_and_nothing_else(tmp_path):
    files = workspace(tmp_path, 'repos:\n  - repo: local\n    modules: [a]\n', {'a': ''})
    (tmp_path / 'modules' / 'a' / 'data').mkdir()

    with pytest.raises(ModuleError, match='meta module.*remove data'):
        check_manifest(*files)


def test_autoupdate_takes_the_newest_tag_and_keeps_the_layout(remote):
    text = f'# pinned\nrepos:\n{entry(remote, "v1.0")}  - repo:    local\n    modules: [a]\n'

    assert get_latest_tag(str(remote)) == 'v1.1'
    assert set_versions(text, {str(remote): 'v1.1'}) == text.replace('v1.0', 'v1.1')


@pytest.mark.parametrize('path, source, error', [
    ('code/main.py', 'from suil.directory import Directory\n', 'code/main.py:1 imports suil.directory'),
    ('tests/test_a.py', 'import suil.cli\n', 'tests/test_a.py:1 imports suil.cli'),
    ('code/main.py', 'x = 1\nrun_command(host, "id")\n', 'code/main.py:2 calls run_command'),
    ('code/main.py', 'from pyinfra.api import get_fact\n', 'code/main.py:1 calls get_fact'),
])
def test_a_module_off_the_contract_is_named(tmp_path, path, source, error):
    files = workspace(tmp_path, 'repos:\n  - repo: local\n    modules: [a]\n', {'a': ''})
    target = tmp_path / 'modules' / 'a' / path
    target.parent.mkdir(parents=True)
    target.write_text(source)

    with pytest.raises(ModuleError, match=error):
        check_manifest(*files)


def test_imports_through_the_sdk_and_testing_pass(tmp_path):
    files = workspace(tmp_path, 'repos:\n  - repo: local\n    modules: [a]\n', {'a': ''})
    (tmp_path / 'modules' / 'a' / 'tests').mkdir()
    (tmp_path / 'modules' / 'a' / 'tests' / 'test_a.py').write_text(
        'import suil.sdk.libs\nfrom suil.testing import get_order\n')

    assert list(check_manifest(*files)) == ['a']
