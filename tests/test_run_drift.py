from suil.libs import module_run_drift

EXPECTED = '''
def expected(config):
    return {'files': {'/etc/x.conf': 'new'}, 'service': {'running': True}}
'''


def module(tmp_path, name, source):
    code = tmp_path / name / 'code'
    code.mkdir(parents=True)
    (code / 'main.py').write_text(source)

    return tmp_path


def test_a_file_the_run_left_behind_is_named(tmp_path):
    modules_dir = module(tmp_path, 'drift_stale', EXPECTED)
    facts = {'files': {'/etc/x.conf': 'old'}, 'service': {'running': True}}

    assert module_run_drift('drift_stale', {}, facts, modules_dir) == ['files./etc/x.conf']


def test_facts_matching_expected_are_no_drift(tmp_path):
    modules_dir = module(tmp_path, 'drift_clean', EXPECTED)
    facts = {'files': {'/etc/x.conf': 'new'}, 'service': {'running': True, 'enabled': True}}

    assert module_run_drift('drift_clean', {}, facts, modules_dir) == []


def test_a_module_without_expected_has_nothing_to_differ(tmp_path):
    modules_dir = module(tmp_path, 'drift_none', 'def deploy(config, facts, force):\n    pass\n')

    assert module_run_drift('drift_none', {}, {}, modules_dir) == []
