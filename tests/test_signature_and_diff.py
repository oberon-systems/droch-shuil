from suil.libs import module_diff_configs, module_get_signature


def test_a_signature_is_stable_across_calls(modules_dir):
    assert module_get_signature('ssh', modules_dir) == module_get_signature('ssh', modules_dir)


def test_two_modules_do_not_share_a_signature(modules_dir):
    assert module_get_signature('ssh', modules_dir) != module_get_signature('packages', modules_dir)


def test_a_changed_file_changes_the_signature(tmp_path):
    root = tmp_path / 'demo' / 'data'
    root.mkdir(parents=True)
    (root / 'defaults.yaml').write_text('demo: {}\n')
    before = module_get_signature('demo', tmp_path)

    (root / 'defaults.yaml').write_text('demo: {a: 1}\n')

    assert module_get_signature('demo', tmp_path) != before


def test_an_equal_config_diffs_to_nothing():
    assert module_diff_configs({'a': {'b': 1}}, {'a': {'b': 1}}) == {}


def test_the_diff_names_the_path_that_differs():
    diff = module_diff_configs({'a': {'b': 1}}, {'a': {'b': 2}})

    assert diff == {('a', 'b'): {'expected': 1, 'actual': 2}}


def test_a_fact_beyond_the_expected_keys_is_not_drift():
    assert module_diff_configs({'a': 1}, {'a': 1, 'b': 2}) == {}


def test_a_missing_fact_is_drift():
    assert module_diff_configs({'a': 1}, {}) == {('a',): {'expected': 1, 'actual': None}}
