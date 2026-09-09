import pytest

from suil.errors import ModuleError, ModuleOrderError
from suil.libs import module_get_order, module_get_requires


def test_base_expands_in_list_order(modules_dir):
    assert module_get_order(['base'], modules_dir) == [
        'hostname', 'repos', 'packages', 'accounts', 'ssh', 'nftables', 'base']


def test_nftables_is_last_and_repos_precedes_packages(modules_dir):
    order = module_get_order(['base'], modules_dir)

    assert order.index('nftables') > order.index('packages')
    assert order.index('accounts') < order.index('ssh')
    assert order.index('repos') < order.index('packages')


def test_packages_declares_repos_rather_than_relying_on_position(modules_dir):
    assert module_get_requires('packages', modules_dir) == ['repos']
    assert module_get_order(['packages'], modules_dir) == ['repos', 'packages']


def test_ssh_declares_accounts_rather_than_relying_on_position(modules_dir):
    assert module_get_requires('ssh', modules_dir) == ['accounts']
    assert module_get_order(['ssh'], modules_dir) == ['accounts', 'ssh']


def test_a_module_that_is_not_there_is_named(modules_dir):
    with pytest.raises(ModuleError, match='nosuchmodule'):
        module_get_order(['nosuchmodule'], modules_dir)


def test_a_cycle_is_reported_as_one(tmp_path):
    for name, requires in (('a', 'b'), ('b', 'a')):
        (tmp_path / name).mkdir()
        (tmp_path / name / 'requires.yaml').write_text(f'requires: [{requires}]\n')

    with pytest.raises(ModuleOrderError, match='cycle'):
        module_get_order(['a'], tmp_path)
