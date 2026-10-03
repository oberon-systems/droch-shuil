# Extracting suil

suil moves out of the inventory repository into its own and is installed
into the workspace as a pinned package. The workspace keeps its data and, for
now, its modules as a `repo: local` entry of `modules.yaml`.

## Today

- suil lives in `suil/` inside the inventory repository and is installed with
  `pip install -e ./suil` by `make install`.
- `suil/pyproject.toml` declares no dependencies: pyinfra, pydantic, PyYAML,
  pyrage, Click and the rest come from the workspace's `requirements.txt`.
- The package directory is the project directory (`package-dir` is `.`), and
  the packages are listed by hand: `suil` and `suil.libs`.
- `make test` runs suil's own tests and every module's tests in one pytest
  call.

## Preconditions

- [02-workspace.md](02-workspace.md): suil finds the workspace from the
  current directory or `--workspace`, never from the location of its source.
- [04-migrate-sdk.md](04-migrate-sdk.md): the runner and the modules import
  only `suil.sdk` and `suil.testing`.
- [05-manifest.md](05-manifest.md): modules are declared in `modules.yaml`.

Without these the extracted package would still reach into the workspace
tree.

## Repository

The new repository gets `suil/` with its history, filtered out of the
inventory repository with `git filter-repo --subdirectory-filter suil`. The
package moves to the usual layout, a `suil/` package directory under the
repository root, so setuptools finds `suil`, `suil.libs` and `suil.sdk`
without a hand-written list.

What moves: the runner, `suil.sdk`, `suil.testing`, `suil/tests/` and
`suil/docs/`. Everything else stays in the workspace: `data/`, `modules/`,
the pre-commit configuration and the Makefile.

## Package

- `pyproject.toml` lists every runtime dependency suil imports, with lower
  bounds. The workspace's `requirements.txt` keeps the exact pins.
- The version follows SemVer and is released from a `vX.Y.Z` tag. The
  first release is `0.2.0`; `SDK_VERSION` moves separately, only when
  `suil.sdk` changes.
- The `suil` console script and the `suil.testing` pytest plugin entry point
  stay as they are.

suil is installed from Git, like the modules, and not from a package index:

```text
suil @ git+https://git.example.com/suil@v0.2.0
```

## CI

The suil repository runs its tests and pre-commit on every push. On a tag it
builds the wheel, installs it into a fresh virtual environment and runs
`suil --help` there before the release is published.

## The workspace after the move

- `requirements.txt` pins suil to a tag. `make install` drops
  `pip install -e ./suil`.
- `make test` runs `pytest modules -q`; the module tests keep their fixtures
  through the plugin of the installed package.
- Working on suil and the workspace at once is `pip install -e ../suil` in
  the workspace's virtual environment, by hand, and never committed.
- `CLAUDE.md` and `README.md` describe suil as an installed tool.

## Non-goals

No module leaves the workspace in this step, and no package index is used.

## Acceptance

- A fresh virtual environment installs suil from its tag and runs
  `suil --help`.
- No import or path in the suil repository refers to the workspace.
- The workspace's `make install` and `make test` pass with suil from the tag,
  and a full role `suil apply --dry-run` writes the same `.runs/` catalogue
  as before the move.
