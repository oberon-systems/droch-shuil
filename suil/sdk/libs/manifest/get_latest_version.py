from suil.sdk.models import Index

from .get_version_key import get_version_key


def get_latest_version(index: Index, name: str) -> str | None:
    versions = [release.version for release in index.modules.get(name, []) if get_version_key(release.version)]

    return max(versions, key=get_version_key, default=None)
