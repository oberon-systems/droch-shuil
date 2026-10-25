import hashlib

from suil.sdk.libs.module import diff_configs, get_signature
from suil.sdk.models import Root


def module(root, name, content):
    data = root / name / 'data'
    data.mkdir(parents=True)
    (data / 'defaults.yaml').write_text(content)

    return Root(name=name, path=root / name)


def test_a_signature_is_stable_across_calls(tmp_path):
    demo = module(tmp_path, 'demo', 'demo: {}\n')

    assert get_signature(demo) == get_signature(demo)


def test_two_modules_do_not_share_a_signature(tmp_path):
    one = module(tmp_path, 'one', 'one: {}\n')
    two = module(tmp_path, 'two', 'two: {}\n')

    assert get_signature(one) != get_signature(two)


def test_a_changed_file_changes_the_signature(tmp_path):
    demo = module(tmp_path, 'demo', 'demo: {}\n')
    before = get_signature(demo)

    (tmp_path / 'demo' / 'data' / 'defaults.yaml').write_text('demo: {a: 1}\n')

    assert get_signature(demo) != before


def test_the_signature_covers_the_files_alone(tmp_path):
    demo = module(tmp_path, 'demo', 'demo: {}\n')

    assert get_signature(demo) == 'sha256:' + hashlib.sha256(b'data/defaults.yaml\0demo: {}\n\0').hexdigest()


def test_an_equal_config_diffs_to_nothing():
    assert diff_configs({'a': {'b': 1}}, {'a': {'b': 1}}) == {}


def test_the_diff_names_the_path_that_differs():
    diff = diff_configs({'a': {'b': 1}}, {'a': {'b': 2}})

    assert diff == {('a', 'b'): {'expected': 1, 'actual': 2}}


def test_a_fact_beyond_the_expected_keys_is_not_drift():
    assert diff_configs({'a': 1}, {'a': 1, 'b': 2}) == {}


def test_a_missing_fact_is_drift():
    assert diff_configs({'a': 1}, {}) == {('a',): {'expected': 1, 'actual': None}}
