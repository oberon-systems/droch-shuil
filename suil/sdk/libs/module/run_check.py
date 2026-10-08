from ...protocols import Checks


def run_check(module: Checks | None, facts: dict) -> list[str]:
    """What the module finds broken on the host, judged from the facts alone."""
    return list(module.check(facts)) if module else []
