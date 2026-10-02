from ...protocols import Expects
from .diff_configs import diff_configs


def run_drift(module: Expects | None, facts: dict) -> list[str]:
    """Every path where the facts still differ from what the module expects."""
    if module is None:
        return []

    return ['.'.join(map(str, path)) for path in diff_configs(module.expected(), facts)]
