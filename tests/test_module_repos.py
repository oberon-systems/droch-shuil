import configparser

import pytest

OS_LAYER = {
    'repos_dir':      '/etc/yum.repos.d',
    'gpg_dir':        '/etc/pki/rpm-gpg',
    'rclone_package': 'rclone',
    'rclone_binary':  '/usr/bin/rclone',
}

STORE = {
    'provider':          'Cloudflare',
    'endpoint':          'https://account.r2.cloudflarestorage.com',
    'bucket':            'repo',
    'access_key_id':     'key',
    'secret_access_key': 'secret',
    'listen':            '127.0.0.1:8083',
}


def config(load, suil_context, **kwargs):
    return load('repos', 'config').Config(suil=suil_context, **OS_LAYER, **kwargs)


def parse(text):
    parser = configparser.ConfigParser()
    parser.read_string(text)

    return parser


def test_a_repository_without_a_source_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, list={'epel': {'gpgcheck': False}})


def test_a_repository_with_two_sources_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, list={'epel': {
            'baseurl': 'https://example.net/', 'metalink': 'https://example.net/m', 'gpgcheck': False}})


def test_an_id_dnf_would_not_accept_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, list={'not a repoid': {
            'baseurl': 'https://example.net/', 'gpgcheck': False}})


def test_a_store_nothing_declares_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, list={'oberon': {'store': 'repo', 'gpgcheck': False}})


def test_gpgcheck_without_a_key_is_refused(load, suil_context):
    # dnf fails the first install on an unknown key, and says nothing useful.
    with pytest.raises(ValueError):
        config(load, suil_context, list={'epel': {'baseurl': 'https://example.net/'}})


def test_a_gpgkey_no_keys_entry_writes_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, list={'oberon': {
            'baseurl': 'https://example.net/',
            'gpgkey':  'file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oberon'}})


def test_a_gpgkey_a_keys_entry_writes_is_accepted(load, suil_context):
    entry = config(
        load, suil_context,
        keys={'RPM-GPG-KEY-oberon': {'content': 'key'}},
        list={'oberon': {'baseurl': 'https://example.net/',
                         'gpgkey': 'file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oberon'}})

    assert entry.list['oberon'].gpgkey == ['file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oberon']


def test_two_stores_on_one_port_are_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, stores={'one': STORE, 'two': dict(STORE, bucket='other')})


def test_a_store_without_credentials_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, stores={'repo': dict(STORE, secret_access_key='')})


def test_the_rendered_file_is_ini_dnf_can_read(load, suil_context):
    main = load('repos')
    entry = config(load, suil_context, list={'epel': {
        'description': 'Extra Packages $releasever',
        'metalink':    'https://mirrors.example.net/metalink?repo=epel-$releasever',
        'gpgkey':      ['https://example.net/KEY-1', 'https://example.net/KEY-2'],
        'priority':    10,
        'options':     {'countme': 1},
    }})

    parsed = parse(main.render_repo(entry, 'epel', entry.list['epel']))

    assert parsed['epel']['name'] == 'Extra Packages $releasever'
    assert parsed['epel']['metalink'] == 'https://mirrors.example.net/metalink?repo=epel-$releasever'
    assert parsed['epel']['gpgkey'] == 'https://example.net/KEY-1 https://example.net/KEY-2'
    assert parsed['epel']['gpgcheck'] == '1'
    assert parsed['epel']['priority'] == '10'
    assert parsed['epel']['countme'] == '1'
    assert 'baseurl' not in parsed['epel']


def test_a_store_backed_repository_points_at_the_loopback_front(load, suil_context):
    main = load('repos')
    entry = config(load, suil_context, stores={'repo': STORE}, list={'oberon': {
        'store': 'repo', 'path': '/rpm/rocky/10/x86_64/', 'gpgcheck': False}})

    parsed = parse(main.render_repo(entry, 'oberon', entry.list['oberon']))

    assert parsed['oberon']['baseurl'] == 'http://127.0.0.1:8083/rpm/rocky/10/x86_64/'
    # dnf aborts a whole transaction over one repository it cannot reach, and
    # the front is not up yet when the first run installs rclone.
    assert parsed['oberon']['skip_if_unavailable'] == '1'


def test_a_plain_repository_keeps_dnfs_own_skip_default(load, suil_context):
    main = load('repos')
    entry = config(load, suil_context, list={'local': {
        'baseurl': 'file:///srv/repo/x86_64', 'gpgcheck': False}})

    assert 'skip_if_unavailable' not in parse(
        main.render_repo(entry, 'local', entry.list['local']))['local']


def test_the_unit_runs_rclone_read_only_as_the_store_account(load, suil_context):
    main = load('repos')
    entry = config(load, suil_context, stores={'repo': STORE})
    unit = main.render_unit(entry, 'repo', entry.stores['repo'])

    assert 'User=balor-repo' in unit
    assert '/usr/bin/rclone serve http --read-only' in unit
    assert '--addr 127.0.0.1:8083' in unit
    assert 'repo:repo' in unit
    assert 'CacheDirectory=repo-repo-balor' in unit


def test_expected_carries_the_shape_the_collector_prints(load, suil_context):
    main = load('repos')
    entry = config(
        load, suil_context,
        keys={'RPM-GPG-KEY-oberon': {'content': 'key'}},
        stores={'repo': STORE},
        list={'oberon': {'store': 'repo', 'path': 'rpm', 'gpgcheck': False},
              'gone': {'ensure': 'absent'}})

    expected = main.expected(entry)

    assert set(expected) == {'keys', 'list', 'stores', 'unmanaged'}
    assert expected['list']['gone'] == {'ensure': 'absent', 'digest': None}
    assert expected['stores']['repo']['service'] == {'running': True, 'enabled': True}
    assert expected['stores']['repo']['listening'] is True
    assert expected['keys']['RPM-GPG-KEY-oberon']['digest'] is not None


def test_a_verbatim_file_reports_no_digest(load, suil_context):
    main = load('repos')
    entry = config(load, suil_context, list={'docker-ce': {
        'file': {'url': 'https://download.docker.com/linux/centos/docker-ce.repo'}}})

    assert main.expected(entry)['list']['docker-ce']['digest'] is None
