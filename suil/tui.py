import logging

import questionary

from suil.deployment import Deployment
from suil.directory import Directory

log = logging.getLogger(__name__)


def role_select(directory) -> str | None:
    roles = directory.roles

    if not roles:
        return None

    return questionary.select(
        'Please select a role for run deployment:\n',
        sorted(roles),
        use_jk_keys=False,
        use_search_filter=True,
    ).ask()


def tui(workspace, settings):
    log.info('\n=== Suil: an infrastructure manager ===\n')
    directory = Directory(workspace, role=role_select(Directory(workspace)))

    if not directory.nodes:
        log.warning('nothing to deploy')
        return

    directory.show()

    if not questionary.confirm('Apply?', default=False).ask():
        return

    Deployment(settings, directory).run()
