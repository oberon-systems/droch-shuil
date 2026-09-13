from suil.libs import run_build_directory, run_read_directory
from suil.models import Secret


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
    run_build_directory(catalogue(), tmp_path)
    read = run_read_directory(tmp_path)

    assert list(read) == ['node-01.example.com']
    assert read['node-01.example.com']['public']['demo']['fqdn'] == 'node-01.example.com'
    assert read['node-01.example.com']['modules'] == ['demo']


def test_latest_points_at_the_newest_run(tmp_path):
    directory = run_build_directory(catalogue(), tmp_path)

    assert (tmp_path / 'latest').resolve() == directory.resolve()


def test_a_secret_reaches_the_catalogue_as_a_digest_only(tmp_path, monkeypatch):
    monkeypatch.setattr(Secret, 'reveal', lambda self: 'hunter2')
    entry = catalogue()
    entry['node-01.example.com']['public']['demo']['token'] = Secret('Y2lwaGVy')

    run_build_directory(entry, tmp_path)
    written = (tmp_path / 'latest' / 'node-01.example.com' / 'demo.yaml').read_text()

    assert 'hunter2' not in written
    assert 'Y2lwaGVy' not in written
    assert 'sha256:' in written
