from suil.directory import Directory
from suil.sdk.libs.module import get_defaults
from suil.sdk.libs.run import build_directory, read_directory
from suil.sdk.models import Encrypted, Root
from suil.workspace import Workspace


def catalogue():
    # `public` is what reaches the disk: `configs` in a live catalogue holds the
    # validated models, plaintext secrets and all, and never leaves memory.
    return {
        'node-01.example.com': {
            'role': 'test', 'family': 'redhat', 'release': 10,
            'deployment': {'ssh_user': 'deploy'},
            'modules': ['demo'],
            'public': {'demo': {'fqdn': 'node-01.example.com'}},
        },
    }


def test_a_run_is_written_and_read_back(tmp_path):
    build_directory(catalogue(), tmp_path)
    read = read_directory(tmp_path)

    assert list(read) == ['node-01.example.com']
    assert read['node-01.example.com']['public']['demo']['fqdn'] == 'node-01.example.com'
    assert read['node-01.example.com']['modules'] == ['demo']


def test_latest_points_at_the_newest_run(tmp_path):
    directory = build_directory(catalogue(), tmp_path)

    assert (tmp_path / 'latest').resolve() == directory.resolve()


def test_an_encrypted_value_reaches_the_catalogue_as_a_digest_only(tmp_path, monkeypatch):
    monkeypatch.setattr(Encrypted, 'reveal', lambda self: 'hunter2')
    entry = catalogue()
    entry['node-01.example.com']['public']['demo']['token'] = Encrypted('Y2lwaGVy')

    build_directory(entry, tmp_path)
    written = (tmp_path / 'latest' / 'node-01.example.com' / 'demo.yaml').read_text()

    assert 'hunter2' not in written
    assert 'Y2lwaGVy' not in written
    assert 'sha256:' in written


NODE = 'node-01.example.com'


def workspace(root, monkeypatch, probed=True, site=None):
    files = {
        'data/common.yaml':                     'hierarchy:\n  - os/{family}/{release}.yaml\n'
                                                '  - roles/{role}.yaml\n  - nodes/{node}.yaml\n',
        'data/roles/test.yaml':                 'modules:\n  - demo\n',
        f'data/nodes/{NODE}.yaml':              'role: test\n',
        'modules/demo/requires.yaml':           'requires: []\n',
        'modules/demo/data/defaults.yaml':      'demo:\n  service: none\n  port:    1\n',
        'modules/demo/data/os/redhat/10.yaml':  'demo:\n  service: demod\n  binary:  /usr/bin/demo\n',
    }

    if probed:
        files[f'facts/{NODE}/suil.yaml'] = 'facts:\n  family:  redhat\n  release: 10\n'

    if site:
        files['data/os/redhat/10.yaml'] = site

    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)

    roots = {'demo': Root(name='demo', path=root / 'modules' / 'demo')}
    monkeypatch.setattr('suil.directory.check_manifest', lambda *args: roots)

    return Workspace(root)


def test_the_module_os_layer_is_merged_over_its_defaults(tmp_path, monkeypatch):
    node = Directory(workspace(tmp_path, monkeypatch), node=NODE).nodes[0]

    assert node.demo == {'service': 'demod', 'port': 1, 'binary': '/usr/bin/demo'}


def test_the_workspace_os_layer_wins_over_the_module_one(tmp_path, monkeypatch):
    site = 'demo:\n  binary: /opt/demo\n'
    node = Directory(workspace(tmp_path, monkeypatch, site=site), node=NODE).nodes[0]

    assert node.demo == {'service': 'demod', 'port': 1, 'binary': '/opt/demo'}


def test_an_unprobed_node_reads_no_module_os_layer(tmp_path, monkeypatch):
    node = Directory(workspace(tmp_path, monkeypatch, probed=False), node=NODE).nodes[0]

    assert node.demo == {'service': 'none', 'port': 1}


def test_the_defaults_glob_never_reaches_the_os_directory(tmp_path, monkeypatch):
    workspace(tmp_path, monkeypatch)
    root = Root(name='demo', path=tmp_path / 'modules' / 'demo')

    assert get_defaults(root) == {'demo': {'service': 'none', 'port': 1}}
    assert get_defaults(root, 'redhat') == get_defaults(root)
    assert get_defaults(root, 'debian', 12) == get_defaults(root)
