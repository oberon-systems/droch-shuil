import tempfile

from pathlib import Path

from suil.sdk.errors import ManifestError
from suil.sdk.models import Repo

from .get_checkout import get_checkout
from .get_revision import get_revision
from .run_git import run_git


def install_repo(repo: Repo, cache_dir: Path) -> Path | None:
    """Clone a repository at its version into the cache; None when it is there already."""
    target = get_checkout(cache_dir, repo.repo, repo.version)

    if target.is_dir():
        return None

    target.parent.mkdir(parents=True, exist_ok=True)

    # Cloned beside the target and renamed into place, so a failed install leaves nothing behind.
    with tempfile.TemporaryDirectory(dir=target.parent, prefix='.install-') as temp:
        clone = Path(temp) / 'checkout'
        cloned = run_git('clone', '--quiet', '--no-checkout', repo.repo, str(clone))

        if cloned.returncode != 0:
            raise ManifestError(f'cannot clone {repo.repo}:\n{cloned.stderr.strip()}')

        checked = run_git('-C', str(clone), 'checkout', '--quiet', '--detach', get_revision(clone, repo))

        if checked.returncode != 0:
            raise ManifestError(f'cannot check out {repo.repo} {repo.version}:\n{checked.stderr.strip()}')

        clone.rename(target)

    return target
