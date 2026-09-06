import re

from pathlib import Path

import yaml

from suil.errors import DataError
from suil.models import Lookup, Secret, Tagged

# The block form is a plain string by the time PyYAML is done with it: a folded
# scalar collapses the newlines and leaves '!ENC[ <b64> ]\n'.
BLOCK_ENC = re.compile(r'^\s*!ENC\[\s*[A-Za-z0-9+/=\s]+?\s*\]\s*$')


class SuilLoader(yaml.SafeLoader):
    pass


def _enc_tag(loader, suffix, node):
    # '!ENC[b64]' with no space goes into the TAG NAME whole, leaving an empty
    # scalar - so the ciphertext is the tag suffix, minus the closing bracket.
    return Secret(suffix.rstrip(']'))


def _tagged(strategy):
    def constructor(loader, node):
        if isinstance(node, yaml.SequenceNode):
            value = loader.construct_sequence(node, deep=True)
        elif isinstance(node, yaml.MappingNode):
            value = loader.construct_mapping(node, deep=True)
        else:
            value = loader.construct_scalar(node) or None

        return Tagged(strategy, value)

    return constructor


def _lookup(loader, node):
    return Lookup(loader.construct_mapping(node, deep=True)
                  if isinstance(node, yaml.MappingNode) else loader.construct_scalar(node))


SuilLoader.add_multi_constructor('!ENC[', _enc_tag)
SuilLoader.add_constructor('!LOOKUP', _lookup)

for _strategy in Tagged.STRATEGIES:
    SuilLoader.add_constructor('!' + _strategy, _tagged(_strategy))


def _scan(value):
    if isinstance(value, dict):
        return {key: _scan(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_scan(item) for item in value]

    if isinstance(value, Tagged):
        return Tagged(value.strategy, _scan(value.value))

    if isinstance(value, str) and not isinstance(value, Secret) and BLOCK_ENC.match(value):
        return Secret(value)

    return value


def yaml_load(file: Path) -> dict | None:
    # A hierarchy layer is optional: a missing file is an empty layer.
    if not Path(file).is_file():
        return None

    with open(file) as stream:
        try:
            data = yaml.load(stream, Loader=SuilLoader)
        except yaml.YAMLError as error:
            raise DataError(f'{file} is not readable YAML: {error}') from error

    if data is not None and not isinstance(data, dict):
        raise DataError(f'{file} must hold a mapping, got {type(data).__name__}')

    return _scan(data) if data else data
