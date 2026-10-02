import pytest

from suil.sdk.errors import DataError
from suil.sdk.libs.yaml import load_data
from suil.sdk.models import Tagged


def write(tmp_path, text):
    path = tmp_path / 'layer.yaml'
    path.write_text(text)

    return path


def test_a_key_with_only_comments_under_it_is_loud(tmp_path):
    file = write(tmp_path, 'deployment:\n  #ssh_host: 192.0.2.1\n  #ssh_user: deploy\n')

    with pytest.raises(DataError, match=r'layer\.yaml: deployment has no value'):
        load_data(file)


def test_the_nested_path_is_named(tmp_path):
    with pytest.raises(DataError, match=r': a\.b\.c has no value'):
        load_data(write(tmp_path, 'a:\n  b:\n    c:\n'))


def test_a_null_inside_a_list_is_named(tmp_path):
    with pytest.raises(DataError, match=r': items\.1 has no value'):
        load_data(write(tmp_path, 'items:\n  - one\n  -\n'))


def test_an_empty_strategy_tag_other_than_delete_is_loud(tmp_path):
    with pytest.raises(DataError, match=r': value has no value'):
        load_data(write(tmp_path, 'value: !replace\n'))


def test_deliberate_empties_pass(tmp_path):
    data = load_data(write(tmp_path, 'mapping: {}\nsequence: []\n'))

    assert data == {'mapping': {}, 'sequence': []}


def test_delete_passes(tmp_path):
    data = load_data(write(tmp_path, 'value: !delete\n'))

    assert data == {'value': Tagged('delete', None)}


def test_an_empty_file_is_still_an_empty_layer(tmp_path):
    assert load_data(write(tmp_path, '# nothing here\n')) is None
    assert load_data(tmp_path / 'nothing.yaml') is None
