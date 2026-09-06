import pytest

from suil.errors import DataError
from suil.libs import yaml_load
from suil.models import Secret, Tagged


def write(tmp_path, text):
    path = tmp_path / 'layer.yaml'
    path.write_text(text)

    return path


def test_a_missing_layer_is_an_empty_layer(tmp_path):
    assert yaml_load(tmp_path / 'nothing.yaml') is None


def test_the_inline_enc_form_lands_in_the_tag_name(tmp_path):
    data = yaml_load(write(tmp_path, 'value: !ENC[SGVsbG8=]\n'))

    assert isinstance(data['value'], Secret)
    assert str(data['value']) == 'SGVsbG8='


def test_the_block_enc_form_is_caught_by_the_post_parse_scan(tmp_path):
    data = yaml_load(write(tmp_path, 'value: >\n  !ENC[\n  SGVsbG8=\n  ]\n'))

    assert isinstance(data['value'], Secret)
    assert 'SGVsbG8=' in str(data['value'])


def test_strategy_tags_survive_the_load(tmp_path):
    data = yaml_load(write(tmp_path, 'value: !replace\n  - 1\n'))

    assert data['value'] == Tagged('replace', [1])


def test_broken_yaml_is_loud(tmp_path):
    with pytest.raises(DataError):
        yaml_load(write(tmp_path, 'value: [1\n'))


def test_a_layer_that_is_not_a_mapping_is_loud(tmp_path):
    with pytest.raises(DataError):
        yaml_load(write(tmp_path, '- one\n- two\n'))
