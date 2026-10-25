from pydantic import BaseModel, ConfigDict, model_validator

LOCAL = 'local'


class Repo(BaseModel):
    """One entry of modules.yaml: `local` with a list of modules, or an HTTP source with a version per module."""

    model_config = ConfigDict(extra='forbid')

    repo:    str
    modules: list[str] | dict[str, str]

    @property
    def local(self) -> bool:
        return self.repo == LOCAL

    @property
    def names(self) -> list[str]:
        return list(self.modules)

    @model_validator(mode='after')
    def check_pinned(self) -> 'Repo':
        if self.local:
            if not isinstance(self.modules, list):
                raise ValueError('a local repo lists its modules without versions')

            return self

        if not self.repo.startswith(('http://', 'https://')):
            raise ValueError(f'repo {self.repo!r} is neither local nor an http(s) URL')

        if not isinstance(self.modules, dict):
            raise ValueError(f'{self.repo} pins every module: modules is a map of name: version')

        if unpinned := sorted(name for name, version in self.modules.items() if not version):
            raise ValueError(f"{self.repo}: {', '.join(unpinned)} need a version")

        return self
