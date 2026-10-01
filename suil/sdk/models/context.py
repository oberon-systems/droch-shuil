from pydantic import BaseModel, ConfigDict


class Context(BaseModel):
    """Node identity, injected into every module config by the runner."""

    model_config = ConfigDict(extra='forbid')

    node:     str
    role:     str | None = None
    family:   str
    release:  int
    ssh_user: str | None = None
