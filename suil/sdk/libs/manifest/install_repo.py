import shutil
import tempfile

from pathlib import Path

from suil.sdk.errors import ManifestError
from suil.sdk.models import Repo

from .get_revision import get_revision
from .run_git import run_git


def install_repo(repo: Repo, modules_dir: Path) -> list[str]:
    """Lay the modules of a repository at its version into modules/, replacing what is there."""
    with tempfile.TemporaryDirectory(prefix='suil-install-') as temp:
        clone = Path(temp) / 'clone'
        cloned = run_git('clone', '--quiet', '--no-checkout', repo.repo, str(clone))

        if cloned.returncode != 0:
            raise ManifestError(f'cannot clone {repo.repo}:\n{cloned.stderr.strip()}')

        checked = run_git('-C', str(clone), 'checkout', '--quiet', '--detach', get_revision(clone, repo))

        if checked.returncode != 0:
            raise ManifestError(f'cannot check out {repo.repo} {repo.version}:\n{checked.stderr.strip()}')

        if missing := [name for name in repo.modules if not (clone / 'modules' / name).is_dir()]:
            raise ManifestError(f"modules.yaml: {', '.join(missing)} not in modules/ of {repo.repo} {repo.version}")

        for name in repo.modules:
            shutil.rmtree(Path(modules_dir) / name, ignore_errors=True)
            shutil.copytree(clone / 'modules' / name, Path(modules_dir) / name)

    return repo.modules
