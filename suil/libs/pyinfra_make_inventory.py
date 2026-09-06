from pyinfra.api import Inventory

# What data/common.yaml calls a connection setting, and what the ssh connector
# calls it. Anything else under `deployment` is passed through untouched.
TRANSLATED = {
    'ssh_accept_unknown_hosts': ('ssh_strict_host_key_checking',
                                 lambda value: 'accept-new' if value else 'yes'),
}


def pyinfra_make_inventory(nodes: dict) -> Inventory:
    """nodes: {name: deployment dict} -> a pyinfra inventory of those hosts."""
    hosts = []

    for name, deployment in nodes.items():
        data = {}

        for key, value in (deployment or {}).items():
            if key in TRANSLATED:
                target, convert = TRANSLATED[key]
                data[target] = convert(value)
            else:
                data[key] = value

        data.setdefault('ssh_hostname', data.pop('ssh_host', name))
        hosts.append((name, data))

    return Inventory((hosts, {}))
