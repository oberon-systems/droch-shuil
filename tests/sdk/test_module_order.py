import pytest

from suil.sdk.errors import ModuleError, ModuleOrderError
from suil.sdk.libs.module import get_order
from suil.sdk.models import Root


def tree(root, modules):
    """The roots of empty modules, each with its own requires."""
    for name, requires in modules.items():
        (root / name).mkdir()

        if requires is not None:
            (root / name / 'requires.yaml').write_text('requires: [{}]\n'.format(', '.join(requires)))

    return {name: Root(name=name, path=root / name) for name in modules}


def test_a_requirement_lands_before_what_needs_it(tmp_path):
    roots = tree(tmp_path, {'one': ['two'], 'two': None})

    assert get_order(['one'], roots) == ['two', 'one']


def test_the_order_of_a_requires_list_is_the_order_of_the_run(tmp_path):
    roots = tree(tmp_path, {'meta': ['first', 'second', 'third'],
                            'first': None, 'second': None, 'third': None})

    assert get_order(['meta'], roots) == ['first', 'second', 'third', 'meta']


def test_a_module_is_ordered_once_however_often_it_is_required(tmp_path):
    roots = tree(tmp_path, {'one': ['shared'], 'two': ['shared'], 'shared': None})

    assert get_order(['one', 'two'], roots) == ['shared', 'one', 'two']


def test_a_module_that_is_not_there_is_named(tmp_path):
    roots = tree(tmp_path, {'one': ['nosuchmodule']})

    with pytest.raises(ModuleError, match='nosuchmodule'):
        get_order(['one'], roots)


def test_a_cycle_is_reported_as_one(tmp_path):
    roots = tree(tmp_path, {'a': ['b'], 'b': ['a']})

    with pytest.raises(ModuleOrderError, match='cycle'):
        get_order(['a'], roots)
