from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .repo import LOCAL


class Root(BaseModel):
    """Where a declared module lives, and the repository and version it came from."""

    model_config = ConfigDict(frozen=True)

    name:    str
    path:    Path
    repo:    str = LOCAL
    version: str | None = None
