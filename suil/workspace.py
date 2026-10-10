from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_cache_dir

from suil.errors import WorkspaceError

COMMON = """---
deployment:
  ssh_port:                 22
  ssh_user:                 deploy
  ssh_accept_unknown_hosts: yes

hierarchy:
  - os/{family}/{release}.yaml
  - modules/{module}.yaml
  - roles/{role}.yaml
  - nodes/{node}.yaml
"""


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

    def init(self) -> None:
        """Lay out an empty workspace; refuses where any part of one already is."""
        if found := [path.name for path in (self.data_dir, self.modules_dir, self.manifest) if path.exists()]:
            raise WorkspaceError(f"{self.base_dir} already holds {', '.join(found)}: nothing written")

        for layer in ('os', 'modules', 'roles', 'nodes'):
            (self.data_dir / layer).mkdir(parents=True)

        self.modules_dir.mkdir()
        (self.data_dir / 'common.yaml').write_text(COMMON)
