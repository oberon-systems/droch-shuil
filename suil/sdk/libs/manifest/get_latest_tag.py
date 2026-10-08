from suil.sdk.errors import ManifestError

from .run_git import run_git


def get_latest_tag(url: str) -> str | None:
    listed = run_git('ls-remote', '--tags', '--refs', '--sort=-version:refname', url)

    if listed.returncode != 0:
        raise ManifestError(f'cannot list the tags of {url}:\n{listed.stderr.strip()}')

    refs = [line.split('\t')[1] for line in listed.stdout.splitlines() if '\t' in line]

    return refs[0].removeprefix('refs/tags/') if refs else None
