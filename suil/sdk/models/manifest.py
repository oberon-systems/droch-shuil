from pydantic import BaseModel, ConfigDict, model_validator

from .repo import Repo


class Manifest(BaseModel):
    """modules.yaml: the repositories a workspace takes its modules from."""

    model_config = ConfigDict(extra='forbid')

    repos: list[Repo]

    @model_validator(mode='after')
    def check_unique(self) -> 'Manifest':
        names = [name for repo in self.repos for name in repo.modules]

        if twice := sorted({name for name in names if names.count(name) > 1}):
            raise ValueError(f"declared twice: {', '.join(twice)}; keep each module in one repo")

        return self
