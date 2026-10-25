from pydantic import BaseModel, ConfigDict


class Release(BaseModel):
    """One version of a module in an index: its archive, relative to the source or absolute, and its digest."""

    model_config = ConfigDict(extra='forbid')

    version: str
    url:     str
    sha256:  str
