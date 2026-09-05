import questionary

from suil.config import cfg
from suil.deployment import deployment
from suil.libs import roles_collect


def select(message: str, choices) -> list[str]:
    if not choices:
        return []

    return questionary.checkbox(
        message,
        sorted(choices),
        use_jk_keys=False,
        use_search_filter=True,
    ).ask() or []


def roles_select() -> list[str]:
    return select(
        'Please select roles for a list for run deployment:\n',
        roles_collect(cfg.roles_dir),
    )


def tui():
    questionary.print('\n=== Balor Suil: an infrastructure manager ===\n\n')

    return deployment(roles=roles_select())
