from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Root(BaseModel):
    """Where a declared module lives: always modules/<name> of the workspace."""

    model_config = ConfigDict(frozen=True)

    name: str
    path: Path
