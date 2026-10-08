import hashlib

from pathlib import Path


def get_checkout(cache_dir: Path, url: str, version: str) -> Path:
    """One checkout per repository and version: <cache>/<url digest>/<version>."""
    return Path(cache_dir) / hashlib.sha256(url.encode()).hexdigest()[:16] / version
