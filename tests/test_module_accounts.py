import pytest


def config(load, suil_context, **kwargs):
    return load('accounts', 'config').Config(suil=suil_context, **kwargs)


def test_a_password_that_is_not_a_crypt_hash_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, users={'deploy': {'password': 'REDACTED'}})


def test_a_key_that_is_not_a_public_key_is_refused(load, suil_context):
    with pytest.raises(ValueError):
        config(load, suil_context, users={'deploy': {'auth_key': 'REDACTED'}})


def test_removing_the_connecting_account_is_refused(load, suil_context):
    with pytest.raises(ValueError, match='absent'):
        config(load, suil_context, users={'deploy': {'state': 'absent'}})


def test_the_guard_can_be_turned_off_deliberately(load, suil_context):
    entry = config(load, suil_context, lockout_check=False,
                   users={'deploy': {'state': 'absent'}})

    assert entry.users['deploy'].state == 'absent'


def test_one_group_may_be_written_as_a_string(load, suil_context):
    entry = config(load, suil_context, users={'zombig': {'groups': 'wheel'}})

    assert entry.users['zombig'].groups == ['wheel']


def test_expected_carries_digests_and_never_a_secret(load, suil_context):
    main = load('accounts')
    key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB8 deploy'
    entry = config(load, suil_context, users={
        'zombig': {'auth_key': key, 'sudo': 'zombig ALL=(ALL) NOPASSWD: ALL'},
        'ubuntu': {'state': 'absent'},
    })

    reported = main.expected(entry)['users']

    assert reported['ubuntu'] == {'state': 'absent'}
    assert reported['zombig']['auth_key'].startswith('sha256:')
    assert key not in str(reported)
