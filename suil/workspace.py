from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_cache_dir


@dataclass(frozen=True)
class Workspace:

    base_dir: Path = field(default_factory=Path.cwd)
    cache_dir: Path = field(default_factory=lambda: Path(user_cache_dir('suil')))

    @property
    def data_dir(self):
        return self.base_dir / 'data'

    @property
    def manifest(self):
        return self.base_dir / 'modules.yaml'

    @property
    def modules_dir(self):
        return self.base_dir / 'modules'

    @property
    def facts_dir(self):
        return self.base_dir / 'facts'

    @property
    def runs_dir(self):
        return self.base_dir / '.runs'
