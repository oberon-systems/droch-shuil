# Moving modules out

The modules leave the workspace's `modules/` tree and move into their own Git
repositories, one repository per group. The workspace then installs them
through `modules.yaml` like any other source. The move goes one group at a
time and stays reversible until `modules/` is removed.

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

## Groups

- **base** - `base`, `hostname`, `selinux`, `repos`, `packages`, `ssh`,
  `accounts`, `nftables`. The whole `base` run order, nftables last included,
  stays in one repository and moves in one step.
- **services** - `docker`, `nginx`, `unbound`. They require `repos` and
  `nftables` from base.
- **vpn** - `client-vpn`, `amneziawg`, `xray`, `awg-keeper`. They require
  `repos` from base, and `client-vpn` requires `docker` and `nginx` from
  services.

Every module is in exactly one group. A `requires` entry may name a module of
another group: module names in `modules.yaml` are one namespace whatever
repository a module comes from.

## Moving a group

1. The group's directories are cut out of the workspace history with
   `git filter-repo`, into a new repository with one directory per module at
   its root.
2. The repository gets its first tag, `v1.0.0`.
3. In `modules.yaml` the group's modules leave the `repo: local` entry and get
   an entry of their own with the repository URL and `version: v1.0.0`.
4. `suil install` fetches the repository into the cache.
5. Module names do not change, so `data/` is not touched: roles and nodes
   select the same names, and encrypted values stay where they are.

The groups move in the order base, services, vpn, so every group finds what
it requires already moved or still in `modules/`.

## Checking a group

After each group every role must resolve the same module order and write the
same `node.yaml` and `<module>.yaml` under `.runs/` on
`suil apply --dry-run` as before the group moved. The module signatures do
change, because they now cover the repository URL and the `version`, so the
first real run forces every moved module once.

## Rollback

A rollback is the previous `modules.yaml`, restored from Git. The group's
directories are still in `modules/` until the last step, so the `local` entry
picks them up again, and nothing on a node or in the cache needs a hand.

## Removing modules/

The moved directories stay in `modules/`, unused, until a full run of every
role on the new sources converges with `nothing to apply`. Then `modules/` and
the `repo: local` entry are removed from the workspace, and module tests run
in each module repository's own CI.

## Acceptance

- `modules.yaml` has three Git entries, base, services and vpn, each pinned to
  a tag, and no `local` entry.
- A clean clone of the workspace runs `suil install` and gets every module
  without module code in its own tree.
- Every role resolves the same module order and the same `.runs/` catalogue
  as before the move.
