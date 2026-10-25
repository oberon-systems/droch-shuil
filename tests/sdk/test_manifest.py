import hashlib
import io
import os
import tarfile
import threading

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest
import yaml

from suil.sdk.errors import ManifestError, ModuleError, ModuleOrderError
from suil.sdk.libs.manifest import (check_manifest, get_latest_version, install_module, pack_module, read_index,
                                    read_manifest, set_versions, write_index)
from suil.sdk.models import Index, Release


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def module(base, name, requires='', extra=''):
    (base / name).mkdir(parents=True, exist_ok=True)
    (base / name / 'requires.yaml').write_text(f'requires: [{requires}]\n{extra}')


def serve(directory):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, f'http://127.0.0.1:{server.server_port}'


@pytest.fixture
def source(tmp_path):
    """A source serving one 1.0.0 and 1.1.0 and two 1.0.0, packed from a module repository."""
    repo, dist = tmp_path / 'src' / 'modules', tmp_path / 'dist'
    module(repo, 'one', 'two')
    module(repo, 'two')
    pack_module('one-1.0.0', repo, dist)
    pack_module('two-1.0.0', repo, dist)
    module(repo, 'one', 'two', '# 1.1.0\n')
    pack_module('one-1.1.0', repo, dist)
    write_index(dist)
    server, url = serve(dist)

    yield url, dist, server

    server.shutdown()
    server.server_close()


def workspace(tmp_path, text, local=None):
    for name, requires in (local or {}).items():
        module(tmp_path / 'modules', name, requires)

    (tmp_path / 'modules.yaml').write_text(text)

    return tmp_path / 'modules.yaml', tmp_path / 'modules'


def entry(url, one='1.0.0', two='1.0.0'):
    return f'  - repo:    {url}\n    modules:\n      one:    {one}\n      two:    {two}\n'


def install(file, modules):
    for repo in read_manifest(file).repos:
        if not repo.local:
            index = read_index(repo.repo)

            for name, version in repo.modules.items():
                install_module(repo.repo, index, name, version, modules)


def test_a_source_lays_its_modules_into_modules_and_validates_with_the_server_gone(tmp_path, source):
    url, _, server = source
    file, modules = workspace(tmp_path, 'repos:\n' + entry(url, one='1.1.0'))

    with pytest.raises(ManifestError, match='module one is not in modules/; run suil install'):
        check_manifest(file, modules)

    install(file, modules)
    server.shutdown()

    assert {name: root.path for name, root in check_manifest(file, modules).items()} == {
        'one': modules / 'one', 'two': modules / 'two'}
    assert (modules / 'one' / 'requires.yaml').read_text().endswith('# 1.1.0\n')


def test_an_install_replaces_what_is_there(tmp_path, source):
    file, modules = workspace(tmp_path, 'repos:\n' + entry(source[0]))
    module(modules, 'one')
    (modules / 'one' / 'stale').write_text('')

    install(file, modules)

    assert sorted(path.name for path in (modules / 'one').iterdir()) == ['requires.yaml']


def test_a_version_missing_from_the_index_is_named(tmp_path, source):
    file, modules = workspace(tmp_path, 'repos:\n' + entry(source[0], one='9.9.9'))

    with pytest.raises(ManifestError, match='one 9.9.9 is not in the index'):
        install(file, modules)


def test_a_wrong_sha256_lays_nothing(tmp_path, source):
    url, *_ = source
    index = read_index(url)
    index.modules['one'][0].sha256 = '0' * 64

    with pytest.raises(ManifestError, match='sha256'):
        install_module(url, index, 'one', '1.1.0', tmp_path / 'modules')

    assert not (tmp_path / 'modules').exists()


def test_an_archive_holding_more_than_its_module_lays_nothing(tmp_path, source):
    url, dist, _ = source
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name in ('one', 'evil'):
            tar.addfile(_directory(name))

    (dist / 'bad.tar.gz').write_bytes(buffer.getvalue())
    digest = hashlib.sha256(buffer.getvalue()).hexdigest()
    index = Index(modules={'one': [Release(version='2.0.0', url='bad.tar.gz', sha256=digest)]})

    with pytest.raises(ManifestError, match='must hold one/ and nothing else'):
        install_module(url, index, 'one', '2.0.0', tmp_path / 'modules')

    assert not (tmp_path / 'modules').exists()


def _directory(name):
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE

    return info


def test_a_name_declared_twice_is_refused(tmp_path):
    text = 'repos:\n' + entry('https://modules.example.com') + '  - repo: local\n    modules: [one]\n'
    file, _ = workspace(tmp_path, text)

    with pytest.raises(ManifestError, match='declared twice: one'):
        read_manifest(file)


@pytest.mark.parametrize('text', [
    'repos:\n  - repo: https://modules.example.com\n    modules: [one]\n',
    'repos:\n  - repo: https://modules.example.com\n    modules: {one: }\n',
    'repos:\n  - repo: git@example.com:m.git\n    modules: {one: 1.0.0}\n',
    'repos:\n  - repo: local\n    modules: {one: 1.0.0}\n',
    'repos:\n  - repo: local\n    version: v1\n    modules: [one]\n',
])
def test_a_source_pins_every_module_and_local_lists_them(tmp_path, text):
    file, _ = workspace(tmp_path, text)

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


def test_autoupdate_moves_each_module_on_its_own_and_keeps_the_layout(source):
    index = read_index(source[0])
    text = f'# pinned\nrepos:\n{entry(source[0])}  - repo:    local\n    modules: [a]\n'

    assert get_latest_version(index, 'one') == '1.1.0'
    assert get_latest_version(index, 'two') == '1.0.0'
    assert get_latest_version(index, 'three') is None
    assert set_versions(text, {'one': '1.1.0'}) == text.replace('one:    1.0.0', 'one:    1.1.0')


def test_the_newest_version_is_by_semver_not_by_order():
    releases = [Release(version=version, url='x', sha256='x') for version in ('1.9.0', '1.10.0-rc1', '1.10.0', 'x')]

    assert get_latest_version(Index(modules={'one': releases}), 'one') == '1.10.0'


def test_a_tag_packs_its_own_module_and_not_a_longer_namesake(tmp_path):
    repo = tmp_path / 'modules'
    module(repo, 'nginx')
    module(repo, 'nginx-extra')

    with tarfile.open(pack_module('nginx-extra-1.0.0', repo, tmp_path / 'dist')) as tar:
        assert {member.name.split('/')[0] for member in tar.getmembers()} == {'nginx-extra'}

    with tarfile.open(pack_module('nginx-1.0.0', repo, tmp_path / 'dist')) as tar:
        assert {member.name.split('/')[0] for member in tar.getmembers()} == {'nginx'}

    with pytest.raises(ManifestError, match='is not <module>-<semver>'):
        pack_module('nginx-extra', repo, tmp_path / 'dist')


def test_a_rebuild_has_the_same_sha256(tmp_path):
    repo = tmp_path / 'modules'
    module(repo, 'one')
    (repo / 'one' / '__pycache__').mkdir()
    (repo / 'one' / '__pycache__' / 'x.pyc').write_text('')
    first = pack_module('one-1.0.0', repo, tmp_path / 'a').read_bytes()
    os.utime(repo / 'one' / 'requires.yaml', (0, 1_000_000_000))

    assert pack_module('one-1.0.0', repo, tmp_path / 'b').read_bytes() == first

    with tarfile.open(tmp_path / 'a' / 'one-1.0.0.tar.gz') as tar:
        assert sorted(tar.getnames()) == ['one', 'one/requires.yaml']


def test_merge_keeps_the_live_releases(tmp_path, source):
    url, *_ = source
    repo = tmp_path / 'next' / 'modules'
    module(repo, 'one', 'two', '# 1.2.0\n')
    pack_module('one-1.2.0', repo, tmp_path / 'next' / 'dist')

    assert write_index(tmp_path / 'next' / 'dist', url) == ['one-1.2.0']

    index = yaml.safe_load((tmp_path / 'next' / 'dist' / 'index.yaml').read_text())

    assert [release['version'] for release in index['modules']['one']] == ['1.2.0', '1.1.0', '1.0.0']
    assert [release['version'] for release in index['modules']['two']] == ['1.0.0']


def test_merge_with_no_live_index_starts_one(tmp_path, source):
    url, *_ = source
    repo = tmp_path / 'next' / 'modules'
    module(repo, 'one')
    pack_module('one-1.0.0', repo, tmp_path / 'next' / 'dist')

    assert write_index(tmp_path / 'next' / 'dist', f'{url}/nowhere') == ['one-1.0.0']


def test_a_released_version_with_other_bytes_is_refused(tmp_path, source):
    url, *_ = source
    repo = tmp_path / 'next' / 'modules'
    module(repo, 'one', 'two', '# changed\n')
    pack_module('one-1.1.0', repo, tmp_path / 'next' / 'dist')

    with pytest.raises(ManifestError, match='already released with another sha256'):
        write_index(tmp_path / 'next' / 'dist', url)


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
