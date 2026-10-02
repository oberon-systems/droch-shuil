from pyinfra.api.deploy import add_deploy

from ...protocols import Deploys


def run_code(state, host, module: Deploys | None, facts: dict, force: bool) -> bool:
    """Queue the module's operations for one host. False means a meta module.

    `facts` is what the collector reported before the run, empty under --force.
    `force` asks for everything; what that means is the module's call.
    """
    if module is None:
        return False

    add_deploy(state, module.deploy, facts, force, host=host)

    return True
