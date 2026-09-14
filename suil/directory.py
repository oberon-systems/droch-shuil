from suil.config import cfg
from suil.libs import (config_expand_lookups, deep_merge, deep_merge_unwrap, inventory_lookup,
                       module_get_defaults, module_get_order, nodes_collect, role_get_nodes, yaml_load_data)


class NodeStorage:
    def __init__(self, **kwargs):

        data = {
            'role': None,
            'modules': [],
            'family': None,
            'release': None,
            'deployment': {},
        }

        data.update(kwargs)

        self.__dict__.update(data)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)


class RoleStorage:
    def __init__(self, **kwargs):
        data = {
            'name': None,
            'nodes': set(),
            'modules': [],
        }

        data.update(kwargs)

        self.__dict__.update(data)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)


class Directory:
    def __init__(self):
        self._nodes = {}
        self._roles = {}
        self._views = {}
        self._common = None

    @property
    def common(self) -> dict:
        if self._common is None:
            self._common = yaml_load_data(cfg.hierarchy_file) or {}
        return self._common

    @property
    def hierarchy(self) -> list[str]:
        return self.common.get('hierarchy', [])

    def roles(self, name: str) -> RoleStorage:
        fresh = name not in self._roles
        role = self._role(name)

        if fresh:
            # a node loaded before its role has resolved against nothing
            for node in self._nodes.values():
                if node.role == name:
                    self.resolve(node)

        return role

    def _role(self, name: str) -> RoleStorage:
        """Read the role file and nothing else. Re-resolving is roles()' job,
        and a lookup must be able to reach a role without triggering it."""
        if name not in self._roles:
            data = yaml_load_data(cfg.roles_dir / (name + '.yaml')) or {}

            self._roles[name] = RoleStorage(
                name=name,
                nodes=role_get_nodes(name, cfg.nodes_dir),
                **data,
            )

        return self._roles[name]

    def node(self, name: str) -> NodeStorage:
        if name not in self._nodes:
            file = cfg.nodes_dir / (name + '.yaml')
            data = yaml_load_data(file) or {}

            node = NodeStorage(name=name, **data)

            if node.role:
                self.roles(node.role)

            self._nodes[name] = node
            self.resolve(node)

        return self._nodes[name]

    def probe(self, node: NodeStorage, family: str, release: int) -> NodeStorage:
        """Fold in what only the target could tell us, then resolve for real."""
        node.update(family=family, release=release)
        self._views.pop(node.name, None)

        return self.resolve(node)

    def resolve(self, node: NodeStorage) -> NodeStorage:
        data = config_expand_lookups(self._merge(node), self._expander(node.name))
        node.update(**data)

        return node

    @property
    def views(self) -> dict:
        """Every node as the merge left it, lookups NOT expanded. That is what
        keeps a lookup reading another node from recursing into itself."""
        for name in nodes_collect(cfg.nodes_dir):
            self._view(name)

        return self._views

    def _expander(self, name: str):
        def expand(lookup):
            return inventory_lookup(lookup, self.views, name)

        return expand

    def _view(self, name: str) -> dict:
        if name not in self._views:
            data = yaml_load_data(cfg.nodes_dir / (name + '.yaml')) or {}
            self._views[name] = self._merge(NodeStorage(name=name, **data))

        return self._views[name]

    def _merge(self, node: NodeStorage) -> dict:
        role = self._role(node.role) if node.role else None

        declared = (role.modules if role else []) + node.modules
        modules = (module_get_order(declared, cfg.modules_dir)
                   if node.family else self._dedupe(declared))

        layer_vars = {
            'family': node.family,
            'release': node.release,
            'role': node.role,
            'node': node.name,
        }

        data = {'deployment': self.common.get('deployment', {})}

        for module in modules:
            data = deep_merge(data, module_get_defaults(module, cfg.modules_dir))

        for layer in self.hierarchy:
            # a per-module layer is one file per module, the rest carry them all
            for module in (modules if '{module}' in layer else ['']):
                data = deep_merge(data, self.layer(layer, module=module, **layer_vars))

        data = deep_merge_unwrap(data)
        data['modules'] = modules

        return data

    def layer(self, layer: str, **layer_vars) -> dict:
        # An unprobed node has no family yet, so the os layer is simply not read.
        if any(value is None for key, value in layer_vars.items() if '{' + key + '}' in layer):
            return {}

        return yaml_load_data(cfg.data_dir / layer.format(**layer_vars)) or {}

    @staticmethod
    def _dedupe(modules: list[str]) -> list[str]:
        seen = []

        for module in modules:
            if module not in seen:
                seen.append(module)

        return seen


# init directory
directory = Directory()
