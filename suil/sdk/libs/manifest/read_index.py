import yaml

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index

from .read_url import read_url


def read_index(url: str) -> Index:
    """index.yaml of the source at `url`."""
    location = f"{url.rstrip('/')}/index.yaml"

    try:
        return Index(**(yaml.safe_load(read_url(location)) or {}))
    except (TypeError, ValidationError, yaml.YAMLError) as error:
        raise ManifestError(f'{location} is not valid:\n{error}') from error
