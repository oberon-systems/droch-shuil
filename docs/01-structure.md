# Suil structure

How suil is put together today: the run cycle, its entry points, how the
catalogue is built and applied, how lookups resolve and how secrets travel.
The principles behind it are in [00-architecture.md](00-architecture.md).

- [Entry points](#entry-points)
- [Run cycle](#run-cycle)
- [Building the catalogue](#building-the-catalogue)
- [Applying the catalogue](#applying-the-catalogue)
- [Lookups](#lookups)
- [Secrets](#secrets)

## Entry points

Suil installs one console script under two names, `suil` and `droch-shuil`
(both `suil.cli:cli`), and it is entered in one of two ways. Both end in the same function, `deployment()` in
`suil/deployment.py`.

1. **CLI** - `suil <command>`. `apply` runs the full cycle. `config` builds
   the catalogue and prints its public view without connecting. `facts`
   connects and collects facts without changing anything. `nodes`, `modules`,
   `encrypt` and `decrypt` only read local data.
2. **TUI** - `suil` with no command. It offers a checkbox list of the roles
   under `data/roles/` and runs `deployment()` for the chosen ones.

An sdk `Error` raised anywhere ends the process with one colored line,
`suil: <message>`.

## Run cycle

```text
targets        --role/--node -> node names
build          catalogue from local data and the cached OS probe
brief          print nodes and modules, ask "Apply?" (skipped by --confirm)
connect        SSH to every node, probe the OS
rebuild        catalogue again, now with the OS layer
facts          every module's collector runs on every node
run directory  .runs/<timestamp>/ written, latest points at it
queue          each module's deploy() queues operations
apply          pyinfra runs the queue (stops here under --dry-run)
facts again    only for the modules that queued operations
check          check() problems and expected() drift fail the run
```

If no module queued an operation, the run prints `nothing to apply` and goes
straight to the check.

## Building the catalogue

The catalogue is one entry per node: its role, OS family and release, the
connection settings, the ordered module list, each module's validated config
and each module's public config. It is built by `deployment_build()` on top
of the `Directory` in `suil/directory.py`.

### Node and role

The node file `data/nodes/<fqdn>.yaml` names the node's `role`. The role file
`data/roles/<role>.yaml` lists its `modules`; the node may add its own. The
two lists are concatenated, role first.

### OS probe

The OS layer of the data is the one whose variables only the node knows. On
connect, `node_probe_os()` reads `/etc/os-release`, maps it to a family
(`redhat` or `debian`) and a major release, and caches the answer in
`facts/<node>/suil.yaml`. The offline build uses that cache. A node with no
cache is built without the OS layer and its module list is marked
provisional.

### Module order

Once the family is known, `get_order()` walks the `requires.yaml`
graph depth-first and puts every dependency before its dependant. The order
inside a `requires` list is the run order, and a cycle is an error. Without
a family the list is only deduplicated.

### Layers

The node's data is merged bottom to top, each layer deep-merged over the
previous one:

1. `deployment` from `data/common.yaml`;
2. `modules/<m>/data/*.yaml` of every module in the list;
3. the `hierarchy` from `data/common.yaml`, in order: `os/{family}/{release}.yaml`,
   `modules/{module}.yaml` once per module, `roles/{role}.yaml`,
   `nodes/{node}.yaml`.

A missing file is an empty layer. A layer whose variable is not known yet,
like `{family}` before the probe, is skipped.

`deep_merge()` merges dicts recursively and concatenates lists. A YAML tag on
a value changes that: `!replace` overwrites, `!append` concatenates,
`!merge` merges a list of dicts by `name`, `!delete` removes the named items.
After the last layer, `deep_merge_unwrap()` drops any tag left over. Lookups
are expanded last, see [Lookups](#lookups).

### Module configs

Every top-level key of the merged data is a module name. `get_config()`
takes that slice, adds `suil` (node, role, family, release, ssh_user),
decrypts the secrets in it, and validates it with the module's
`code/config.py` `Config`. A meta module, with no code, keeps the plain dict.
`get_public()` then builds the public view of the same config, with
every secret replaced by its digest.

## Applying the catalogue

### Connect

`make_inventory()` turns each node's `deployment` settings into a
pyinfra host, with `ssh_host` or the node name as the address. After the
connect every node is probed and the catalogue is rebuilt with the OS layer.

### Facts before the run

Before collecting, the signature each module recorded last time is read. Then
`collect_facts()` runs for every node and module: it uploads
`facts/collector.py`, the `Facter` bootstrap and the public config, runs the
bootstrap, and parses the JSON it prints. It adds `files`, the sha256
of every path the module's `files()` names. The record goes to
`facts/<node>/<module>.yaml` with a timestamp and the module's current
signature. A collector that fails is reported and the run goes on.

### Run directory

`build_directory()` writes `.runs/<timestamp>/<node>/node.yaml` and one
`<module>.yaml` per module, all public, and points `.runs/latest` at it.

### Queue

For every node and module, `force` is true under `--force` or when the
recorded signature differs from the current one. `run_code()` hands the
module's `deploy(facts, force)` to pyinfra. The module compares `expected()`
with the facts itself and queues only what differs. A module that queued
nothing is skipped in the rest of the run.

### Apply and check

`run_state()` executes the queue; `--dry-run` shows it and stops.
Facts are collected again for the modules that changed. `deployment_check()`
then reads every module's facts: problems from `check()` and paths where
`expected()` still differs are collected, and any of them fail the run with
`DeploymentError`.

## Lookups

A `!LOOKUP` value reads a field from other nodes instead of repeating it. It
takes these keys:

- `field` - the dotted path to read on each node; required.
- `nodes` - a glob over node names, `*` by default.
- `role` - only nodes of this role.
- `ip` - `v4`, `v6` or `any`; keeps only addresses of that family.
- `format` - how each value is rendered, with `{value}`, `{node}` and
  `{role}`; `{value}` by default.
- `self` - `include` (default), `exclude` or `only` the node that asks.

An unknown key or a bad value is a `DataError` when the file is loaded.

The marker passes through the merge untouched. When a node is resolved,
`expand_lookups()` replaces each marker with the list
`lookup()` returns. Inside a list the found values are spliced in
place, next to literal items; anywhere else the marker becomes the list.

A lookup reads the other nodes' *views*: their data merged from their own
node and role files with lookups not expanded and without the OS layer. That
keeps a lookup from reading another lookup and recursing. Matches are
sorted by node name, because the order reaches rendered files and their
digests, and a different order would restart daemons for nothing.

## Secrets

### Encrypting

`suil encrypt '<value>'` encrypts to the age X25519 recipient in
`SUIL_AGE_RECIPIENT` and prints `!ENC[<base64>]`. The value goes into any
data file in place of the plaintext, inline or as a folded block.

### Loading

The YAML loader turns both forms into a `Secret`: a `str` that holds the
ciphertext. Nothing is decrypted on load, and a stray dump of a `Secret`
writes the ciphertext back.

### Using

`get_config()` reveals every secret in the module's slice before
validation, so the module's `Config` holds plaintext. `Secret.reveal()`
decrypts with the private key in `SUIL_AGE_KEY` and keeps the result in
memory. The plaintext never leaves the control machine except inside the
files and operations the module itself sends to the node.

### Public view

Everything that is printed, written or sent to a collector is the public
view. `Secret.digest()` is `sha256:` over the plaintext: enough to see that a
secret changed, not enough to recover it.

- `get_public()` dumps the config with every `Secret` field as its digest.
  It works by field type, so a secret typed anything else is an error.
- `strip_secrets()` replaces any `Secret` that is still left before
  `.runs/` is written.

So the collector on the node, `suil config`, and `.runs/` see digests only.
