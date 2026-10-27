# Suil modules declaration

A workspace declares the modules it uses in one file, `modules.yaml`, the way
[pre-commit](https://pre-commit.com) declares its hook repositories in
`.pre-commit-config.yaml`. suil installs the modules from there over plain
HTTP; it never runs Git. A module carries no manifest of its own: its version
is the one `modules.yaml` pins it to.

## Today

- A module is any directory under `modules/`. What it is follows from which
  files happen to exist: no `code/main.py` makes it a meta module.
- Dependencies live in `requires.yaml`, one list, and nothing else about the
  module is declared.
- Modules have no version, and the only way to use a module is to have it in
  the same repository as the data.
- A missing function, a wrong signature or a typo in a file name shows up only
  when a run reaches that module.

## modules.yaml

`modules.yaml` sits in the workspace root, beside `data/`:

```yaml
repos:
  - repo:    https://modules.example.com/suil
    modules:
      hostname: 0.1.0
      ssh:      0.3.1
  - repo:    local
    modules: [docker, nginx, unbound]
```

- `repo` - the `http(s)://` URL of a source, or `local` for modules written
  in the workspace itself.
- `modules` - for a source, a map of module name to version, so every module
  is pinned on its own; for `local`, a list of the directories under
  `modules/`.

A module is named by its directory name, and a name must be unique across
`modules.yaml`. Roles and nodes keep selecting modules by that name.

Every module lives in `modules/<name>` of the workspace, wherever it came
from. A source is only where `suil install` takes it from, and nothing
after the install knows about it. Whether installed modules are
committed or ignored by Git is the workspace's choice.

## Sources

A source is any static HTTP server: nginx, an object store, anything that
serves files. Under its URL it serves `index.yaml` and one archive per module
version:

```yaml
modules:
  hostname:
    - version: 0.1.1
      url:     hostname-0.1.1.tar.gz
      sha256:  9f2c...
    - version: 0.1.0
      url:     hostname-0.1.0.tar.gz
      sha256:  41ab...
```

- `url` - the archive, relative to the source URL or absolute.
- An archive `<name>-<version>.tar.gz` holds `<name>/` and nothing else, never
  the repository the module is written in.

## Module version

A module's version is the one `modules.yaml` pins it to, a semver version
released from a `<module>-<version>` tag. There is no `module.yaml` inside the
module and nothing in it to keep in step with the tag. The signature covers
the module's files alone, so a new version forces the module once on every
node only where its files changed.

## Installation

`suil install` reads the index of every source, downloads the archive of each
module at its version, checks its `sha256`, and lays it into `modules/`,
replacing what is there. It does nothing for `local`. An archive whose digest
differs, or that holds anything besides its module, lays nothing.

`suil autoupdate` moves every module of a source to the newest version in the
index, compared by semver, and rewrites `modules.yaml` line by line, so its
layout and comments stay; nothing else changes a version.

`suil config`, `suil facts` and `suil apply` never touch the network. They
read modules from `modules/` only, and fail with the `suil install` command
to run when a declared module is not there.

## Validation

`suil validate` checks the declaration and every module it names, and
connects to no node.

- `modules.yaml` parses, every module of a source has a version, and `local`
  lists its modules without one.
- Every declared module is in `modules/`, every directory there is declared,
  and no name is declared twice.
- Every `requires.yaml` entry names a declared module, and the graph has no
  cycle.
- Every module with code implements the interfaces from
  [03-sdk.md](03-sdk.md), each method with its protocol's signature.
- A module with no code has a `requires.yaml` and nothing but it, its
  `README.md`, its `tests/` and its release files `.cz.yaml` and
  `CHANGELOG.md`.
- A module imports suil only through `suil.sdk` and `suil.testing`, in its
  code, its collector and its tests.
- Nothing under a module's `code/` reads the node: `get_fact`,
  `run_command` and `host_run_command` belong in `facts/collector.py`.

Each failure names the module, the file and what to change. `suil config`,
`suil facts` and `suil apply` run the same validation before they build the
catalogue.

## Publishing

A module repository keeps its modules under `modules/<name>` and its
`index.yaml` at the root, committed. A module is released with `cz bump` in
its directory: the version comes from the `version:` of its `.cz.yaml`, and a
pre-bump hook records the release in `index.yaml`, so the bump commit and its
tag `<name>-<version>` carry the index. Publishing packs the tagged module
and uploads it with that `index.yaml`; the live source is never read back.

```yaml
# modules/<name>/.cz.yaml
commitizen:
  version:        0.1.0
  tag_format:     <name>-$version
  pre_bump_hooks:
    - cd ../.. && .venv/bin/suil index "$CZ_PRE_NEW_TAG_VERSION" && git add index.yaml
```

```shell
suil index hostname-0.1.1   # index.yaml: hostname 0.1.1 and its sha256
suil pack hostname-0.1.1    # dist/hostname-0.1.1.tar.gz and dist/index.yaml
```

Both run at the root of the module repository.

- `suil index TAG` - the module is the directory under `modules/` the tag
  starts with, followed by a semver version, so `nginx-extra-1.0.0` is never
  `nginx`; the version must be the one in its `.cz.yaml`. It packs the module
  and adds or replaces its release in `index.yaml`, every other release kept.
- `suil pack TAG` - packs the same module into `dist/` and copies
  `index.yaml` beside it. A release `index.yaml` does not hold, or a module
  whose bytes differ from what it records, is an error: the module changed
  after its bump. The archive has the same bytes on every build: sorted
  entries, mtime 0, owner 0, no `__pycache__`.

Uploading `dist/` is the publisher's: suil names no host. The upload adds the
archive and replaces `index.yaml`; the archives already there stay.

### On any CI

Any CI, or a workstation, runs the same steps on a checkout of the module
repository at the tag; the GitHub action below is these steps.

```shell
pip install droch-shuil          # Python 3.11 or newer
suil pack "$TAG"                 # TAG is <module>-<version>
rsync -a dist/ "$UPLOAD_TARGET"  # or any upload that reaches the source URL
```

### GitHub Actions

droch-shuil ships the packing as the action `publish`. Its venv is cached in
the calling repository, so a release installs droch-shuil once per version.
The upload is the next step, with whatever action reaches the source; here
the source is a GitHub release:

```yaml
on:
  push:
    tags: ["*-*"]

permissions:
  contents: write

concurrency:
  group: publish-modules

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - id: suil
        uses: oberon-systems/droch-shuil/publish@v0.7.3
      - uses: softprops/action-gh-release@v2
        with:
          tag_name: modules
          files: ${{ steps.suil.outputs.dir }}/*
```

The action installs the droch-shuil of its own ref, so pin it to a tag, or
set `suil-version`.

### GitLab CI

The steps above as a job:

```yaml
publish:
  image: python:3.12
  resource_group: publish-modules
  rules:
    - if: $CI_COMMIT_TAG
  script:
    - pip install droch-shuil
    - suil pack "$CI_COMMIT_TAG"
    - rsync -a dist/ "$UPLOAD_TARGET"
```

### Locally

The same steps by hand, from the root of the module repository checked out at
the tag. The GitHub
workflow itself runs on a workstation with
[act](https://github.com/nektos/act), given a tag push event:

```shell
act push --eventpath tag.json   # {"ref": "refs/tags/hostname-0.1.1"}
```

## Migration

The workspace gets a `modules.yaml` with one `repo: local` entry listing
every directory under `modules/`. Nothing moves and nothing is renamed, so the
resolved module order of every role stays the same. Moving modules into their
own repositories is a later step of the plan.

## Acceptance

- `modules.yaml` declares every module under `modules/`, and a directory it
  does not declare is an error.
- `suil validate` passes on the tree and runs in CI through pre-commit.
- Every role resolves the same module order and the same `.runs/` catalogue
  as before the change.
- A source serving archives built by `suil pack` and `suil index` installs
  into `modules/`, and validates with the server gone, in tests against a
  local HTTP server.
