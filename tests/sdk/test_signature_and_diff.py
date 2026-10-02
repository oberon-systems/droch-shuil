from suil.sdk.libs.module import diff_configs, get_signature


def module(root, name, content):
    data = root / name / 'data'
    data.mkdir(parents=True)
    (data / 'defaults.yaml').write_text(content)

    return root


def test_a_signature_is_stable_across_calls(tmp_path):
    module(tmp_path, 'demo', 'demo: {}\n')

    assert get_signature('demo', tmp_path) == get_signature('demo', tmp_path)


def test_two_modules_do_not_share_a_signature(tmp_path):
    module(tmp_path, 'one', 'one: {}\n')
    module(tmp_path, 'two', 'two: {}\n')

    assert get_signature('one', tmp_path) != get_signature('two', tmp_path)


def test_a_changed_file_changes_the_signature(tmp_path):
    module(tmp_path, 'demo', 'demo: {}\n')
    before = get_signature('demo', tmp_path)

    (tmp_path / 'demo' / 'data' / 'defaults.yaml').write_text('demo: {a: 1}\n')

    assert get_signature('demo', tmp_path) != before


def test_an_equal_config_diffs_to_nothing():
    assert diff_configs({'a': {'b': 1}}, {'a': {'b': 1}}) == {}


def test_the_diff_names_the_path_that_differs():
    diff = diff_configs({'a': {'b': 1}}, {'a': {'b': 2}})

    assert diff == {('a', 'b'): {'expected': 1, 'actual': 2}}


def test_a_fact_beyond_the_expected_keys_is_not_drift():
    assert diff_configs({'a': 1}, {'a': 1, 'b': 2}) == {}


def test_a_missing_fact_is_drift():
    assert diff_configs({'a': 1}, {}) == {('a',): {'expected': 1, 'actual': None}}
