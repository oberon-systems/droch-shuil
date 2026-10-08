from pydantic import BaseModel, ConfigDict, model_validator

LOCAL = 'local'


class Repo(BaseModel):
    """One entry of modules.yaml: a Git repository pinned to a tag or SHA, or `local`."""

    model_config = ConfigDict(extra='forbid')

    repo:    str
    version: str | None = None
    modules: list[str]

    @property
    def local(self) -> bool:
        return self.repo == LOCAL

    @model_validator(mode='after')
    def check_pinned(self) -> 'Repo':
        if self.repo.startswith('-'):
            raise ValueError(f'repo {self.repo!r} is not a Git URL')

        if self.local and self.version is not None:
            raise ValueError('a local repo takes no version: drop it')

        if not self.local and not self.version:
            raise ValueError(f'{self.repo} needs a version: a tag or a 40-character SHA')

        return self
