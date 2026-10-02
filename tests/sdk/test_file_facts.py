import hashlib

from suil.sdk.libs.module import file_digest, file_needs_write

CONTENT = 'listen 443\n'
DIGEST = hashlib.sha256(CONTENT.encode()).hexdigest()


def test_the_digest_is_what_sha256_says_of_the_file_and_none_is_no_file():
    assert file_digest(CONTENT) == DIGEST
    assert file_digest(CONTENT.encode()) == DIGEST
    assert file_digest(None) is None


def test_a_file_the_facts_already_hold_is_not_written():
    assert not file_needs_write({'files': {'/etc/x': DIGEST}}, '/etc/x', CONTENT)


def test_a_changed_or_missing_file_is_written():
    assert file_needs_write({'files': {'/etc/x': 'other'}}, '/etc/x', CONTENT)
    assert file_needs_write({'files': {'/etc/x': None}}, '/etc/x', CONTENT)
    assert file_needs_write({}, '/etc/x', CONTENT)


def test_a_file_that_must_go_is_a_write_only_while_it_is_there():
    assert file_needs_write({'files': {'/etc/x': DIGEST}}, '/etc/x', None)
    assert not file_needs_write({'files': {'/etc/x': None}}, '/etc/x', None)


def test_force_writes_whatever_the_facts_say():
    assert file_needs_write({'files': {'/etc/x': DIGEST}}, '/etc/x', CONTENT, force=True)
