# Extracting suil

suil moved out of the inventory repository into its own, and is published to
PyPI as `droch-shuil`. The workspace installs it as a pinned package and keeps
its data and, for now, its modules as a `repo: local` entry of
`modules.yaml`.

## Before

- suil lived in `suil/` inside the inventory repository and was installed
  with `pip install -e ./suil` by `make install`.
- `suil/pyproject.toml` declared no dependencies: pyinfra, pydantic, PyYAML,
  pyrage, Click and the rest came from the workspace's `requirements.txt`.
- The package directory was the project directory (`package-dir` was `.`),
  and the packages were listed by hand.
- `make test` ran suil's own tests and every module's tests in one pytest
  call.

## Preconditions

- [02-workspace.md](02-workspace.md): suil finds the workspace from the
  current directory, never from the location of its source.
- [04-migrate-sdk.md](04-migrate-sdk.md): the runner and the modules import
  only `suil.sdk` and `suil.testing`.
- [05-manifest.md](05-manifest.md): modules are declared in `modules.yaml`.

Without these the extracted package would still reach into the workspace
tree.

## Repository

The new repository took `suil/` with its history. A fresh clone of the
inventory repository was filtered with `git filter-repo`, keeping `suil/` and
renaming paths on the way to the usual layout:

- `suil/` stays the package directory;
- `suil/tests/` becomes `tests/`;
- `suil/docs/` becomes `docs/`;
- `suil/pyproject.toml` becomes `pyproject.toml`.

The filtered history was merged into the new repository, whose tooling was
already committed, as one merge commit. Every commit that touched `suil/`
keeps its message, author and date.

What stays in the workspace: `data/`, `modules/`, its pre-commit
configuration, its Makefile, and the two tests that check the modules of a
workspace rather than suil itself.

## Package

- The distribution is `droch-shuil`: PyPI refuses `suil` as too close to an
  existing name. The import package stays `suil`.
- It installs one console script under two names, `suil` and `droch-shuil`,
  and keeps the `suil.testing` pytest plugin entry point.
- `pyproject.toml` lists every runtime dependency suil imports, with lower
  bounds. setuptools finds `suil` and its sub-packages without a list.
- The version follows SemVer and is released from a `vX.Y.Z` tag. The
  first release is `0.2.0`; `SDK_VERSION` moves separately, only when
  `suil.sdk` changes.

## CI

- A `vX.Y.Z` tag runs `.github/workflows/publish.yml`. It checks that the
  tag matches the version in `pyproject.toml`, builds the sdist and the
  wheel, installs the wheel into a fresh virtual environment, runs
  `suil --help` and `droch-shuil --help`, and publishes to PyPI through
  trusted publishing.
- A push to `main` that changes `docs/`, `README.md` or `mkdocs.yml`
  publishes the documentation to GitHub Pages.
- The tests and the pre-commit hooks run locally, through `make test` and
  `make lint`.

## The workspace after the move

- `requirements.txt` pins `droch-shuil` to a release. `make install` drops
  `pip install -e ./suil`.
- `make test` runs `pytest modules -q`; the module tests keep their fixtures
  through the plugin of the installed package.
- Working on suil and the workspace at once is `pip install -e ../suil` in
  the workspace's virtual environment, by hand, and never committed.
- `CLAUDE.md` and `README.md` describe suil as an installed tool.

## Non-goals

No module leaves the workspace in this step.

## Acceptance

- A fresh virtual environment installs `droch-shuil` from PyPI and runs
  `suil --help` and `droch-shuil --help`.
- No import or path in the suil repository refers to the workspace.
- The workspace's `make install` and `make test` pass with the released
  package, and a full role `suil apply --dry-run` writes the same `.runs/`
  catalogue as before the move.
