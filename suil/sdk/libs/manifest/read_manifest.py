from pathlib import Path

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Manifest

from ..yaml.load import load


def read_manifest(file: Path) -> Manifest:
    if not Path(file).is_file():
        raise ManifestError(f'{file} does not exist: declare the modules of the workspace there')

    try:
        return Manifest(**(load(file) or {}))
    except (TypeError, ValidationError) as error:
        raise ManifestError(f'{file} is not valid:\n{error}') from error
