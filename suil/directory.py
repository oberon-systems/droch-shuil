import copy
import logging

from pathlib import Path

from suil.errors import DataError, DirectoryError
from suil.libs import (config_expand_lookups, deep_merge, deep_merge_unwrap, module_get_defaults,
                       module_get_facts, module_get_order, yaml_load_data)

log = logging.getLogger(__name__)


def counted(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


class NodeStorage:
    def __init__(self, **kwargs):

        data = {
            'role': None,
            'modules': [],
            'family': None,
            'release': None,
            'facts': False,
            'deployment': {},
        }

        data.update(kwargs)

        self.__dict__.update(data)


class Directory:
    """One run, every node of it resolved through the hierarchy when it is made.

    Nothing changes it afterwards but probe(), and what it hands out is a copy.
    """

    def __init__(self, workspace, role=None, node=None):
        if role and node:
            raise DirectoryError('give a role or a node, not both')

        common = yaml_load_data(workspace.data_dir / 'common.yaml') or {}

        object.__setattr__(self, '_workspace', workspace)
        object.__setattr__(self, '_common', common)
        object.__setattr__(self, '_hierarchy', tuple(common.get('hierarchy', [])))

        names = (node,) if node else ()

        if role:
            self.resolve(self._pattern('role'), required=True, role=role)
            names = tuple(name for name, found in self.inventory.items() if found == role)

        merged = {}

        for name in names:
            probe = module_get_facts(name, 'suil', workspace.facts_dir).get('facts') or {}
            merged[name] = self._merge(name, probe.get('family'), probe.get('release'))

        object.__setattr__(self, '_merged', merged)
        object.__setattr__(self, '_nodes', {})

        self._lookup(*names)

    def __setattr__(self, name, value):
        raise AttributeError('a Directory does not change once it is made')

    @property
    def workspace(self):
        return self._workspace

    @property
    def nodes(self) -> tuple[NodeStorage, ...]:
        return tuple(copy.deepcopy(node) for node in self._nodes.values())

    @property
    def roles(self) -> set[str]:
        return {path.stem for path in self._workspace.data_dir.glob(self._pattern('role').format(role='*'))}

    @property
    def inventory(self) -> dict[str, str | None]:
        paths = sorted(self._workspace.data_dir.glob(self._pattern('node').format(node='*')))

        return {path.stem: (yaml_load_data(path) or {}).get('role') for path in paths}

    def probe(self, name: str, family: str, release: int) -> NodeStorage:
        """The one change a Directory takes: the OS layer, which only the target knows."""
        self._merged[name] = self._merge(name, family, release)
        self._lookup(name)

        return copy.deepcopy(self._nodes[name])

    def resolve(self, pattern: str, required: bool = False, **kwargs) -> Path | None:
        path = self._workspace.data_dir / pattern.format(**kwargs)

        if path.is_file():
            return path

        if required:
            raise DataError(f'{path.relative_to(self._workspace.base_dir)} does not exist')

        return None

    def show(self) -> None:
        seen, blind = [], []

        log.info('\n=== deployment ===\n')

        for node in self._nodes.values():
            line = f'{node.name} ({node.role}, '

            if node.facts:
                log.info(line + f'{node.family} {node.release})')
            else:
                log.warning(line + 'no facts)')
                blind.append(node.name)

            for module in node.modules:
                log.info(f'  {module}')

                if module not in seen:
                    seen.append(module)

            log.info('')

        log.info(f"{counted(len(self._nodes), 'node')}, {counted(len(seen), 'module')}")

        if blind:
            log.warning('no facts for: ' + ', '.join(blind))
            log.warning('the modules above are provisional - the exact set and order '
                        'are known only after the facts are collected')

        log.info('')

    def _pattern(self, key: str) -> str:
        for layer in self._hierarchy:
            if '{' + key + '}' in layer:
                return layer

        raise DataError(f'the hierarchy in data/common.yaml has no {{{key}}} layer')

    def _lookup(self, *names: str) -> None:
        for name in names:
            self._nodes[name] = NodeStorage(name=name, **config_expand_lookups(self._merged[name], self._merged, name))

    def _merge(self, name: str, family: str | None, release: int | None) -> dict:
        modules_dir = self._workspace.modules_dir
        node = yaml_load_data(self.resolve(self._pattern('node'), required=True, node=name)) or {}
        role = node.get('role')
        role_data = yaml_load_data(self.resolve(self._pattern('role'), required=True, role=role)) or {} if role else {}

        declared = (role_data.get('modules') or []) + (node.get('modules') or [])
        modules = module_get_order(declared, modules_dir) if family else self._dedupe(declared)

        layer_vars = {
            'family': family,
            'release': release,
            'role': role,
            'node': name,
        }

        data = {'deployment': self._common.get('deployment', {})}

        for module in modules:
            data = deep_merge(data, module_get_defaults(module, modules_dir))

        for layer in self._hierarchy:
            # a per-module layer is one file per module, the rest carry them all
            for module in (modules if '{module}' in layer else ['']):
                data = deep_merge(data, self._layer_data(layer, module=module, **layer_vars))

        data = deep_merge_unwrap(data)
        data.update(modules=modules, role=role, family=family, release=release, facts=family is not None)

        return data

    def _layer_data(self, layer: str, **layer_vars) -> dict:
        # An unprobed node has no family yet, so the os layer is simply not read.
        if any(value is None for key, value in layer_vars.items() if '{' + key + '}' in layer):
            return {}

        path = self.resolve(layer, **layer_vars)

        return (yaml_load_data(path) or {}) if path else {}

    @staticmethod
    def _dedupe(modules: list[str]) -> list[str]:
        seen = []

        for module in modules:
            if module not in seen:
                seen.append(module)

        return seen
