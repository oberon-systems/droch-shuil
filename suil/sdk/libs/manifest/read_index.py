import yaml

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index

from .read_url import read_url


def read_index(url: str, missing_ok: bool = False) -> Index:
    """index.yaml of the source at `url`; an empty one when it is not there yet and `missing_ok`."""
    location = f"{url.rstrip('/')}/index.yaml"

    try:
        return Index(**(yaml.safe_load(read_url(location, b'' if missing_ok else None)) or {}))
    except (TypeError, ValidationError, yaml.YAMLError) as error:
        raise ManifestError(f'{location} is not valid:\n{error}') from error
