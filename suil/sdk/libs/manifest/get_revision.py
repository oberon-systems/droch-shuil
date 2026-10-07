import re

from pathlib import Path

from suil.sdk.errors import ManifestError
from suil.sdk.models import Repo

from .run_git import run_git

SHA = re.compile(r'[0-9a-f]{40}')


def get_revision(checkout: Path, repo: Repo) -> str:
    """The commit `version` names in a clone: a tag or a full SHA, never a branch."""
    ref = repo.version if SHA.fullmatch(repo.version) else f'refs/tags/{repo.version}'
    found = run_git('-C', str(checkout), 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}')

    if found.returncode == 0:
        return found.stdout.strip()

    branch = run_git('-C', str(checkout), 'rev-parse', '--verify', '--quiet', f'refs/remotes/origin/{repo.version}')
    what = 'a branch, which pins nothing' if branch.returncode == 0 else 'neither a tag nor a commit'

    raise ManifestError(f'modules.yaml: {repo.repo} version {repo.version} is {what}; '
                        f'set a tag or a 40-character SHA')
