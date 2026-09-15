"""One function per file, named subject-verb-object."""

# roles related functions
from .roles_collect import roles_collect
from .role_get_nodes import role_get_nodes

# node related functions
from .nodes_collect import nodes_collect
from .node_get_role import node_get_role
from .node_probe_os import node_probe_os

# module related functions
from .module_get_names import module_get_names
from .module_get_defaults import module_get_defaults
from .module_get_requires import module_get_requires
from .module_get_order import module_get_order
from .module_get_signature import module_get_signature
from .module_get_config import module_get_config
from .module_get_public import module_get_public
from .module_get_facts import module_get_facts
from .module_collect_facts import module_collect_facts
from .module_diff_configs import module_diff_configs
from .module_diff_names import module_diff_names
from .module_load_code import module_load_code
from .module_run_code import module_run_code
from .module_run_check import module_run_check
from .module_diff_touches import module_diff_touches
from .module_get_files import module_get_files
from .module_collect_files import module_collect_files
from .module_file_digest import module_file_digest
from .module_file_needs_write import module_file_needs_write
from .module_validate_file import module_validate_file

# run catalogue
from .run_build_directory import run_build_directory, run_read_directory

# pyinfra bridge
from .pyinfra_make_inventory import pyinfra_make_inventory
from .pyinfra_run_state import (pyinfra_connect, pyinfra_make_state,
                                pyinfra_read_failures, pyinfra_run_state)
from .host_put_content import host_put_content
from .host_run_command import host_run_command
from .host_sudo_password import host_sudo_password

# secrets
from .string_encrypt import string_encrypt
from .string_decrypt import string_decrypt
from .config_strip_secrets import config_reveal_secrets, config_strip_secrets

# inventory lookups
from .inventory_lookup import inventory_lookup
from .config_expand_lookups import config_expand_lookups

# misc and utils
from .deep_merge import deep_merge, deep_merge_unwrap
from .yaml_load import yaml_load
from .yaml_load_data import yaml_load_data

__all__ = [
    'roles_collect',
    'role_get_nodes',
    'nodes_collect',
    'node_get_role',
    'node_probe_os',
    'module_get_names',
    'module_get_defaults',
    'module_get_requires',
    'module_get_order',
    'module_get_signature',
    'module_get_config',
    'module_get_public',
    'module_get_facts',
    'module_collect_facts',
    'module_diff_configs',
    'module_diff_names',
    'module_load_code',
    'module_run_code',
    'module_run_check',
    'module_diff_touches',
    'module_get_files',
    'module_collect_files',
    'module_file_digest',
    'module_file_needs_write',
    'module_validate_file',
    'run_build_directory',
    'run_read_directory',
    'pyinfra_make_inventory',
    'pyinfra_connect',
    'pyinfra_make_state',
    'pyinfra_read_failures',
    'pyinfra_run_state',
    'host_put_content',
    'host_run_command',
    'host_sudo_password',
    'string_encrypt',
    'string_decrypt',
    'config_reveal_secrets',
    'config_strip_secrets',
    'inventory_lookup',
    'config_expand_lookups',
    'deep_merge',
    'deep_merge_unwrap',
    'yaml_load',
    'yaml_load_data',
]
