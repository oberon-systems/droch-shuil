from pathlib import Path

from suil.libs import yaml_load
from suil.config import cfg
from suil.errors import DirectoryRoleExists

class NodeStorage:
    def __init__(self, **kwargs):
        
        data = {
            'role': None,
            'modules': [],
            'family': 'redhat',
            'release': 10,
        }
        
        data.update(kwargs)
        
        self.__dict__.update(data)


class RoleStorage:
    def __init__(self, **kwargs):
        data = {
            'role': None,
            'modules': [],
            'family': 'redhat',
            'release': 10,
        }

        data.update(kwargs)

        self.__dict__.update(data)


class Directory:
    def __init__(self):
        self._nodes = {}
        self._role = None
        self._hierarchy = None

    @property
    def hierarchy(self) -> list[str]:
        if not self._hierarchy:
            self._hierarchy = yaml_load(cfg.hierarchy_file)
        return self._hierarchy

    def role(self, name: str) -> RoleStorage:
        if not self._role:
            file = cfg.roles_dir / (name + '.yaml')
            data = yaml_load(file)
            self._role = RoleStorage(**data)

            # todo: update nodes if exist on role load
        return self._role

    def node(self, name: str) -> NodeStorage:
        if not self._nodes.get(name):
            file = cfg.nodes_dir / (name + '.yaml')
            data = yaml_load(file)
            self._nodes[name] = NodeStorage(**data)

            # todo: update loaded node if role already lodaed
            # todo: update modules with hierarchy
            # todo: update modules configs with hierarchy
        return self._nodes[name]


### init directory
directory = Directory()
