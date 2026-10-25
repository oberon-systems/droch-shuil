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

- `repo` - a Git URL, or `local` for modules written in the workspace itself.
- `version` - a tag or a full commit SHA; required for a Git repository,
  absent for `local`. A branch is refused, because it does not pin anything.
- `modules` - the module directories taken from that repository, from its
  `modules/`. Anything else in the repository is ignored.

A module is named by its directory name, and a name must be unique across
`modules.yaml`. Roles and nodes keep selecting modules by that name.

Every module lives in `modules/<name>` of the workspace, wherever it came
from. A Git repository is only where `suil install` takes it from, and
nothing after the install knows about it. Whether installed modules are
committed or ignored by Git is the workspace's choice.

## Module version

A module's version is the `version` of its repository. There is no
`module.yaml` inside the module and nothing in it to keep in step with a tag.
The signature covers the module's files alone, so a new version forces the
module once on every node only where its files changed.

## Installation

`suil install` fetches every Git repository at its `version` and lays the
modules it lists into `modules/`, replacing what is there, and does nothing
for `local`. The clone is temporary and nothing of it is kept.

`suil autoupdate` moves every `version` to the newest tag of its repository and
rewrites `modules.yaml`; nothing else changes a `version`.

`suil config`, `suil facts` and `suil apply` never touch the network. They
read modules from `modules/` only, and fail with the `suil install` command
to run when a declared module is not there.

## Validation

`suil validate` checks the declaration and every module it names, and
connects to no node.

- `modules.yaml` parses and every Git repository has a `version`.
- Every declared module is in `modules/`, every directory there is declared,
  and no name is declared twice.
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
- A Git repository pinned by tag and one pinned by SHA install into
  `modules/`, and validate with the repository gone, in tests against
  temporary repositories.
