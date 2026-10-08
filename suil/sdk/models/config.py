from pydantic import BaseModel, ConfigDict

from .context import Context


class Config(BaseModel):
    """Base of every module's Config. A key the model does not know is an error."""

    model_config = ConfigDict(extra='forbid')

    suil: Context
