from suil.libs import deep_merge, deep_merge_unwrap
from suil.models import Tagged


def test_dicts_merge_recursively():
    assert deep_merge({'a': {'b': 1, 'c': 2}}, {'a': {'c': 3}}) == {'a': {'b': 1, 'c': 3}}


def test_lists_concatenate_lower_first():
    assert deep_merge({'a': [1, 2]}, {'a': [3]}) == {'a': [1, 2, 3]}


def test_scalar_of_the_upper_layer_wins():
    assert deep_merge({'a': 1}, {'a': 2}) == {'a': 2}


def test_append_is_the_default_spelled_out():
    assert deep_merge({'a': [1]}, {'a': Tagged('append', [2])}) == {'a': [1, 2]}


def test_replace_drops_the_lower_list():
    assert deep_merge({'a': [1, 2]}, {'a': Tagged('replace', [3])}) == {'a': [3]}


def test_delete_removes_named_elements():
    assert deep_merge({'a': [1, 2, 3]}, {'a': Tagged('delete', [1, 3])}) == {'a': [2]}


def test_delete_without_a_value_removes_the_key():
    assert deep_merge({'a': [1], 'b': 2}, {'a': Tagged('delete', None)}) == {'b': 2}


def test_merge_joins_lists_of_dicts_by_name():
    lower = {'a': [{'name': 'x', 'v': 1}, {'name': 'y'}]}
    upper = {'a': Tagged('merge', [{'name': 'x', 'w': 2}, {'name': 'z'}])}

    assert deep_merge(lower, upper) == {
        'a': [{'name': 'x', 'v': 1, 'w': 2}, {'name': 'y'}, {'name': 'z'}]}


def test_modules_is_deduplicated_keeping_first_appearance():
    merged = deep_merge({'modules': ['a', 'b']}, {'modules': ['b', 'c', 'a']})

    assert merged['modules'] == ['a', 'b', 'c']


def test_an_unmerged_tag_is_unwrapped():
    assert deep_merge_unwrap({'a': Tagged('replace', [1])}) == {'a': [1]}
