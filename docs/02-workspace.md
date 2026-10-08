# Suil workspace

Suil has to run against a tree it does not live in. This step replaces the
global settings object and the paths derived from suil's own source with an
explicit workspace, passed to every phase of a run.

## Today

- `suil/config.py` builds one global `cfg` at import time. `base_dir` defaults
  to the directory of `config.py` itself, and every other path is a property
  under it: `data/`, `modules/`, `facts/`, `.runs/`.
- `.env` is loaded by `load_dotenv()` as a side effect of importing
  `suil.config`.
- `suil/directory.py` holds a global `directory` that the catalogue build
  fills and reads.
- Library functions reach for `cfg` directly instead of taking the paths they
  need, so two trees cannot be handled in one process, and a test cannot
  point suil at a fixture tree without patching globals.

## Design

A `Workspace` is a frozen record of one tree: its root and the directories
suil reads and writes in it.

- `base_dir` - the workspace directory.
- `data_dir`, `modules_dir`, `manifest` (`modules.yaml`) - read only.
- `facts_dir`, `runs_dir` - written by a run, gitignored.
- `cache_dir` - the suil user cache, where Git modules are installed.

The workspace is the current directory: run suil from the root of the tree.
There is no `--workspace` flag and no `SUIL_WORKSPACE` variable. No path is
ever derived from the location of suil's source.

Settings keep only what is not a path: the age key and recipient, the sudo
password, color. They are read from the environment and from `.env` in the
current directory, once, by the CLI entry point, and not on import.

The workspace and the settings are built once by the CLI and passed down.
`deployment()` and every function under it take what they need as arguments;
`cfg` and the global `directory` are removed. The catalogue build returns a
new directory object per call instead of filling a shared one.

The pytest plugin gains a `workspace` fixture, the workspace of the current
directory, and `modules_dir` becomes `workspace.modules_dir`.

## Non-goals

No new CLI commands or flags, no change to the data layout, no
module distribution. Behaviour on hosts does not change.

## Acceptance

- No code in `suil/` resolves a path relative to its own source.
- Importing any `suil` module reads no file and no environment.
- Two workspaces build their catalogues in one process without sharing
  state.
- A full role `suil apply --dry-run` writes the same `.runs/` catalogue as
  before this step.
