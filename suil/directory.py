from suil.libs import deep_merge, module_get_defaults, role_get_nodes, yaml_load
from suil.config import cfg


class NodeStorage:
    def __init__(self, **kwargs):

        data = {
            'role': None,
            'modules': [],
            'family': 'redhat',
            'release': 10,
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
        self._common = None

    @property
    def common(self) -> dict:
        if self._common is None:
            self._common = yaml_load(cfg.hierarchy_file) or {}
        return self._common

    @property
    def hierarchy(self) -> list[str]:
        return self.common.get('hierarchy', [])

    def roles(self, name: str) -> RoleStorage:
        if name not in self._roles:
            file = cfg.roles_dir / (name + '.yaml')
            data = yaml_load(file) or {}

            self._roles[name] = RoleStorage(
                name=name,
                nodes=role_get_nodes(name, cfg.nodes_dir),
                **data,
            )

            # a node loaded before its role has resolved against nothing
            for node in self._nodes.values():
                if node.role == name:
                    self.resolve(node)

        return self._roles[name]

    def node(self, name: str) -> NodeStorage:
        if name not in self._nodes:
            file = cfg.nodes_dir / (name + '.yaml')
            data = yaml_load(file) or {}

            node = NodeStorage(name=name, **data)

            if node.role:
                self.roles(node.role)

            self._nodes[name] = node
            self.resolve(node)

        return self._nodes[name]

    def resolve(self, node: NodeStorage) -> NodeStorage:
        role = self._roles.get(node.role)

        modules = []
        for module in (role.modules if role else []) + node.modules:
            if module not in modules:
                modules.append(module)

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

        data['modules'] = modules
        node.update(**data)

        return node

    def layer(self, layer: str, **layer_vars) -> dict:
        return yaml_load(cfg.data_dir / layer.format(**layer_vars)) or {}


# init directory
directory = Directory()
