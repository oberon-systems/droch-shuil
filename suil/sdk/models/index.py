from pydantic import BaseModel, ConfigDict

from .release import Release


class Index(BaseModel):
    """index.yaml of a source: the releases of every module, newest first."""

    model_config = ConfigDict(extra='forbid')

    modules: dict[str, list[Release]] = {}
