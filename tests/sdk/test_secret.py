import hashlib

from types import SimpleNamespace

import pytest

from pydantic import BaseModel, ValidationError

from suil.sdk.errors import ModuleConfigError
from suil.sdk.libs.config import reveal_secrets, strip_secrets
from suil.sdk.libs.module import get_config, get_public
from suil.sdk.models import Encrypted, Root, Secret

DIGEST = 'sha256:' + hashlib.sha256(b'pw').hexdigest()


class Fields(BaseModel):
    key:   Secret
    plain: str = ''
    env:   dict[str, Secret | str] = {}
    keys:  list[Secret] = []
    maybe: Secret | None = None


def encrypted(plain: str) -> Encrypted:
    value = Encrypted('cipher-' + plain)
    object.__setattr__(value, '_plain', plain)

    return value


def node(module: str, data: dict):
    return SimpleNamespace(name='test-01.example.com', role='test', family='redhat', release=10,
                           deployment={'ssh_user': 'deploy'}, **{module: data})


def module_dir(tmp_path, module: str, fields: str):
    code = tmp_path / module / 'code'
    code.mkdir(parents=True)
    (code / 'config.py').write_text('from suil.sdk.models import Config, Secret\n\n\n'
                                    f'class Config(Config):\n{fields}\n')

    return Root(name=module, path=tmp_path / module)


def test_a_secret_field_turns_any_string_into_a_secret():
    config = Fields(key='pw', maybe='pw', keys=['pw'])

    assert type(config.key) is Secret
    assert type(config.maybe) is Secret
    assert type(config.keys[0]) is Secret


def test_a_union_keeps_a_secret_and_leaves_a_plain_string_alone():
    config = Fields(key='pw', env={'token': Secret('pw'), 'user': 'admin'})

    assert type(config.env['token']) is Secret
    assert type(config.env['user']) is str


def test_a_str_field_drops_the_secret_type():
    assert type(Fields(key='pw', plain=Secret('pw')).plain) is str


def test_the_public_dump_digests_secrets_and_only_secrets():
    config = Fields(key='pw', env={'token': Secret('pw'), 'user': 'admin'}, maybe='')

    assert config.model_dump(mode='json', context={'public': True}) == {
        'key': DIGEST, 'plain': '', 'env': {'token': DIGEST, 'user': 'admin'}, 'keys': [], 'maybe': ''}
    assert config.model_dump(mode='json')['key'] == 'pw'


def test_strict_validation_takes_only_a_secret():
    with pytest.raises(ValidationError):
        Fields.model_validate({'key': 'pw'}, strict=True)


def test_strip_secrets_digests_models_secrets_and_encrypted_alike():
    assert strip_secrets(Fields(key='pw'))['key'] == DIGEST
    assert strip_secrets({'a': [Secret('pw'), encrypted('pw')], 'b': Secret('')}) == {
        'a': [DIGEST, DIGEST], 'b': ''}


def test_reveal_secrets_hands_out_secrets():
    revealed = reveal_secrets({'a': [encrypted('pw')], 'b': 'open'}, None)

    assert type(revealed['a'][0]) is Secret and revealed['a'][0] == 'pw'
    assert type(revealed['b']) is str


def test_get_config_hands_the_model_secrets_and_get_public_digests_them(tmp_path):
    modules = module_dir(tmp_path, 'vault', '    password: Secret\n    user: str')
    config = get_config(modules, node('vault', {'password': encrypted('pw'), 'user': 'admin'}), None)

    assert type(config.password) is Secret and config.password == 'pw'
    assert get_public(config)['password'] == DIGEST
    assert get_public(config)['user'] == 'admin'


def test_get_config_refuses_an_encrypted_value_in_a_str_field(tmp_path):
    modules = module_dir(tmp_path, 'leaky', '    env: dict[str, str]')

    with pytest.raises(ModuleConfigError, match=r'leaky\.env\.token holds an !ENC value'):
        get_config(modules, node('leaky', {'env': {'token': encrypted('pw')}}), None)


def test_a_meta_module_gets_its_dict_with_secrets(tmp_path):
    config = get_config(Root(name='meta', path=tmp_path / 'meta'), node('meta', {'token': encrypted('pw')}), None)

    assert type(config['token']) is Secret
    assert get_public(config)['token'] == DIGEST
