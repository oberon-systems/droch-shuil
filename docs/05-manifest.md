# Suil modules declaration

A workspace declares the modules it uses in one file, `modules.yaml`, the way
[pre-commit](https://pre-commit.com) declares its hook repositories in
`.pre-commit-config.yaml`. suil installs the modules from there. A module
carries no manifest of its own: its version is the `version` its repository
is pinned to.

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
  - repo:    https://git.example.com/suil-modules
    version: v1.4.0
    modules: [base, hostname, selinux, repos, packages, ssh, accounts, nftables]
  - repo:    https://git.example.com/suil-vpn
    version: 4f3230a9c1d2e8b7a6f5e4d3c2b1a09f8e7d6c5b
    modules: [client-vpn, amneziawg, awg-keeper, xray]
  - repo:    local
    modules: [docker, nginx, unbound]
```

- `repo` - a Git URL, or `local` for modules kept in the workspace under
  `modules/`.
- `version` - a tag or a full commit SHA; required for a Git repository,
  absent for `local`. A branch is refused, because it does not pin anything.
- `modules` - the module directories taken from that repository. Anything
  else in the repository is ignored.

A module is named by its directory name, and a name must be unique across
`modules.yaml`. Roles and nodes keep selecting modules by that name.

## Module version

A module's version is the `version` of its repository. There is no
`module.yaml` inside the module and nothing in it to keep in step with a tag.
A `local` module has no version; its signature alone says when it changed.

The module signature covers the repository URL and the `version` as well as
the module's files, so moving `version` forces the module once on every node.

## Installation

`suil install` clones every Git repository at its `version` into the suil cache,
one checkout per repository and revision, and does nothing for `local`. A
repository and revision already in the cache are not fetched again, so an
install is repeatable offline.

`suil autoupdate` moves every `version` to the newest tag of its repository and
rewrites `modules.yaml`; nothing else changes a `version`.

`suil config`, `suil facts` and `suil apply` never touch the network. They
read modules from the cache and from `modules/`, and fail with the
`suil install` command to run when a declared repository and revision is not
in the cache.

## Validation

`suil validate` checks the declaration and every module it names, and
connects to no node.

- `modules.yaml` parses; every Git repository has a `version`, and no
  `version` is a branch.
- Every declared repository and revision is in the cache.
- Every listed module exists in its repository, and no name is declared
  twice.
- Every `requires.yaml` entry names a declared module, and the graph has no
  cycle.
- Every module with code implements the interfaces from
  [03-sdk.md](03-sdk.md), each method with its protocol's signature.
- A module with no code has a `requires.yaml` and nothing but it, its
  `README.md` and its `tests/`.
- A module imports suil only through `suil.sdk` and `suil.testing`, in its
  code, its collector and its tests.
- Nothing under a module's `code/` reads the node: `get_fact`,
  `run_command` and `host_run_command` belong in `facts/collector.py`.

Each failure names the module, the file and what to change. `suil config`,
`suil facts` and `suil apply` run the same validation before they build the
catalogue.

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
- A Git repository pinned by tag and one pinned by SHA install from a cold
  cache and from a warm one with the network off, in tests against temporary
  repositories.
