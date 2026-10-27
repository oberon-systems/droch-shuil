from pathlib import Path

import yaml

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index


def load_index(file: Path) -> Index:
    """index.yaml of a module repository; an empty one before the first release."""
    try:
        return Index(**(yaml.safe_load(Path(file).read_text()) or {})) if Path(file).is_file() else Index()
    except (TypeError, ValidationError, yaml.YAMLError) as error:
        raise ManifestError(f'{file} is not valid:\n{error}') from error
