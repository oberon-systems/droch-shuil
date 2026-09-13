import pytest

from suil.errors import ModuleError, ModuleOrderError
from suil.libs import module_get_order


def tree(root, modules):
    """A modules directory of empty modules, each with its own requires."""
    for name, requires in modules.items():
        (root / name).mkdir()

        if requires is not None:
            (root / name / 'requires.yaml').write_text('requires: [{}]\n'.format(', '.join(requires)))

    return root


def test_a_requirement_lands_before_what_needs_it(tmp_path):
    tree(tmp_path, {'one': ['two'], 'two': None})

    assert module_get_order(['one'], tmp_path) == ['two', 'one']


def test_the_order_of_a_requires_list_is_the_order_of_the_run(tmp_path):
    tree(tmp_path, {'meta': ['first', 'second', 'third'],
                    'first': None, 'second': None, 'third': None})

    assert module_get_order(['meta'], tmp_path) == ['first', 'second', 'third', 'meta']


def test_a_module_is_ordered_once_however_often_it_is_required(tmp_path):
    tree(tmp_path, {'one': ['shared'], 'two': ['shared'], 'shared': None})

    assert module_get_order(['one', 'two'], tmp_path) == ['shared', 'one', 'two']


def test_a_module_that_is_not_there_is_named(tmp_path):
    tree(tmp_path, {'one': ['nosuchmodule']})

    with pytest.raises(ModuleError, match='nosuchmodule'):
        module_get_order(['one'], tmp_path)


def test_a_cycle_is_reported_as_one(tmp_path):
    tree(tmp_path, {'a': ['b'], 'b': ['a']})

    with pytest.raises(ModuleOrderError, match='cycle'):
        module_get_order(['a'], tmp_path)
