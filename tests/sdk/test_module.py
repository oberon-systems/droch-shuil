import pytest

from suil.sdk.errors import ModuleError
from suil.sdk.libs import module as libs
from suil.sdk.libs.module import get_files, load_class, run_check, run_code, run_drift

HEAD = 'from suil.sdk import Module\n\n\n'

DEMO = HEAD + '''class Demo(Module):

    def deploy(self, facts: dict, force: bool) -> None:
        pass

    def expected(self) -> dict:
        return {'files': {'/etc/x.conf': 'new'}, 'service': {'running': True}}

    def check(self, facts: dict) -> list[str]:
        return [] if facts.get('service', {}).get('running') else ['not running']

    def files(self) -> dict[str, str | bytes | None]:
        return {'/etc/x.conf': 'new', '/etc/old.conf': None}
'''

MANDATORY = '''
    def deploy(self, facts: dict, force: bool) -> None:
        pass

    def expected(self) -> dict:
        return {}
'''


def module(tmp_path, name, source):
    code = tmp_path / name / 'code'
    code.mkdir(parents=True)
    (code / 'main.py').write_text(source)

    return tmp_path


def test_the_one_subclass_is_loaded_and_carries_the_libs(tmp_path):
    cls = load_class('module_demo', module(tmp_path, 'module_demo', DEMO))
    instance = cls({'any': 'config'})

    assert cls.__name__ == 'Demo'
    assert instance.config == {'any': 'config'}
    assert all(getattr(instance, name) is getattr(libs, name) for name in libs.__all__)


def test_a_meta_module_has_no_class(tmp_path):
    (tmp_path / 'module_meta').mkdir()

    assert load_class('module_meta', tmp_path) is None


def test_none_or_two_subclasses_are_refused(tmp_path):
    with pytest.raises(ModuleError, match='found: none'):
        load_class('module_none', module(tmp_path, 'module_none', HEAD))

    two = HEAD + f'class One(Module):\n{MANDATORY}\n\nclass Two(Module):\n{MANDATORY}'

    with pytest.raises(ModuleError, match='found: One, Two'):
        load_class('module_two', module(tmp_path, 'module_two', two))


def test_a_mandatory_method_must_be_overridden(tmp_path):
    source = HEAD + 'class Demo(Module):\n\n    def deploy(self, facts: dict, force: bool) -> None:\n        pass\n'

    with pytest.raises(ModuleError, match=r'does not override expected\(\)'):
        load_class('module_partial', module(tmp_path, 'module_partial', source))


def test_a_signature_other_than_the_protocol_is_refused(tmp_path):
    source = HEAD + f'class Demo(Module):\n{MANDATORY}\n    def check(self, facts) -> list:\n        return []\n'

    with pytest.raises(ModuleError, match=r'Demo\.check\(self, facts\) -> list must be check'):
        load_class('module_signature', module(tmp_path, 'module_signature', source))


def test_drift_check_and_files_come_from_the_instance(tmp_path):
    instance = load_class('module_calls', module(tmp_path, 'module_calls', DEMO))(None)
    facts = {'files': {'/etc/x.conf': 'old'}, 'service': {'running': False}}

    assert run_drift(instance, facts) == ['files./etc/x.conf', 'service.running']
    assert run_drift(instance, {'files': {'/etc/x.conf': 'new'}, 'service': {'running': True}}) == []
    assert run_check(instance, facts) == ['not running']
    assert get_files(instance) == {'/etc/x.conf': 'new', '/etc/old.conf': None}


def test_a_meta_module_does_nothing():
    assert run_drift(None, {'a': 1}) == []
    assert run_check(None, {'a': 1}) == []
    assert get_files(None) == {}
    assert run_code(None, None, None, {}, False) is False
