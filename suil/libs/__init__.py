"""One function per file, named subject-verb-object."""

# roles related functions
from .roles_collect import roles_collect
from .role_get_nodes import role_get_nodes

# node related functions
from .nodes_collect import nodes_collect
from .node_get_role import node_get_role

# module related functions
from .module_get_defaults import module_get_defaults

# misc and utils
from .deep_merge import deep_merge
from .yaml_load import yaml_load

__all__ = [
    'roles_collect',
    'role_get_nodes',
    'nodes_collect',
    'node_get_role',
    'module_get_defaults',
    'deep_merge',
    'yaml_load',
]
