import click
import questionary

from suil.config import cfg
from suil.libs import roles_collect


# Solarized Dark, as truecolor: green, red, yellow, base01.
PALETTE = {
    'ok':   (133, 153, 0),
    'bad':  (220, 50, 47),
    'warn': (181, 137, 0),
    'info': (88, 110, 117),
}


def colored(text: str, kind: str) -> str:
    if not cfg.log_color:
        return text

    return click.style(text, fg=PALETTE[kind])


def ok(text: str) -> None:
    print(colored(text, 'ok'))


def bad(text: str) -> None:
    print(colored(text, 'bad'))


def warn(text: str) -> None:
    print(colored(text, 'warn'))


def info(text: str) -> None:
    print(colored(text, 'info'))


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
    # Imported here, not at module level: deployment.py imports this file back.
    from suil.deployment import deployment

    info('\n=== Balor Suil: an infrastructure manager ===\n')

    return deployment(roles=roles_select())
