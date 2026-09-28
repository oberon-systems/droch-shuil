from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Workspace:

    base_dir: Path = field(default_factory=Path.cwd)

    @property
    def data_dir(self):
        return self.base_dir / 'data'

    @property
    def modules_dir(self):
        return self.base_dir / 'modules'

    @property
    def facts_dir(self):
        return self.base_dir / 'facts'

    @property
    def runs_dir(self):
        return self.base_dir / '.runs'
