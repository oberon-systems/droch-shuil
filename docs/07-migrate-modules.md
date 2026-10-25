# Moving modules out

The modules leave the workspace's own tree and move into one public
repository, released from there to a source over HTTP. The workspace then
installs them through `modules.yaml` like any other source, and they land in the same `modules/<name>` they left. The move
goes one module at a time and stays reversible at every step.

## Today

- Every module lives in the workspace under `modules/`, declared in
  `modules.yaml` as one `repo: local` entry.
- Dependencies between modules are in `requires.yaml`:
  - `base` requires `hostname`, `selinux`, `repos`, `packages`, `ssh`,
    `accounts`, `nftables`;
  - `ssh` requires `accounts`; `packages`, `nginx` and `amneziawg` require
    `repos`; `docker` requires `repos` and `nftables`;
  - `awg-keeper` requires `amneziawg` and `xray`;
  - `client-vpn` requires `amneziawg`, `docker`, `xray`, `awg-keeper`,
    `nginx`.

## The repository

The module repository has the layout of a workspace: every module is
`modules/<name>/`, and its own `modules.yaml` lists them all in one
`repo: local` entry, so `suil validate` and the module tests run there as in
any workspace.

Every module is versioned on its own. Its tags are `<name>-<version>`, its
commitizen config and changelog are in its directory, and a bump counts only
the commits under `modules/<name>/`. A pushed tag is the release: CI packs
the module and adds it to the index of the source, see
[05-manifest.md](05-manifest.md#publishing).

## Moving a module

1. The module's directory is copied into the repository, without history,
   and released with `cz bump`, which tags `<name>-0.1.0`; CI publishes it
   to the source.
2. In the workspace's `modules.yaml` the module leaves the `repo: local`
   entry for the entry of the source, as `<name>: 0.1.0` under its
   `modules`.
3. The workspace stops tracking `modules/<name>/`: whether installed modules
   are committed or ignored by Git is the workspace's choice.
4. `suil install` lays the module back into `modules/<name>`.
5. Module names do not change, so `data/` is not touched: roles and nodes
   select the same names, and encrypted values stay where they are.

Leaves move before what requires them, so a module always finds what it
requires already moved or still local. Meta modules move last.

## Checking a module

After each module every role must resolve the same module order and write the
same `node.yaml` and `<module>.yaml` under `.runs/` on
`suil apply --dry-run` as before the move. The signature covers the module's
files alone, and the installed files are the ones that were tracked, so no
module is forced by the move.

## Rollback

A rollback is the previous `modules.yaml` and the module's directory, both
restored from the workspace's Git history. Nothing on a node needs a hand.

## Acceptance

- Every moved module is pinned to its version under the source entry of the
  workspace's `modules.yaml`; the `local` entry keeps only what the workspace
  writes itself.
- A clean clone of the workspace runs `suil install` and gets every module
  in `modules/`.
- Every role resolves the same module order and the same `.runs/` catalogue
  as before the move, and no module is forced.
