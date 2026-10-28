import yaml

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index

from .read_url import fetch_url


def read_index(url: str) -> Index:
    """index.yaml of the source at `url`."""
    location = f"{url.rstrip('/')}/index.yaml"

    try:
        body, modified = fetch_url(location)
        index = Index(**(yaml.safe_load(body) or {}))
    except (TypeError, ValidationError, yaml.YAMLError) as error:
        raise ManifestError(f'{location} is not valid:\n{error}') from error

    index.modified = modified

    return index
