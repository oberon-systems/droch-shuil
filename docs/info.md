# Suil data and runs

Suil provisions Linux hosts from declarative data. This page describes the
data a workspace holds, how suil resolves it into the configuration of a run,
and how a run applies that configuration node by node.

## Data layer

A workspace is the directory suil is started in. Suil reads and writes only
four directories and one file under it:

```text
<workspace>/
  data/               site data, read only
    common.yaml       connection defaults and the hierarchy
    os/               one file per OS family and release
    modules/          one file per module
    roles/            one file per role
    nodes/            one file per node, named by its FQDN
  modules/            module code and module defaults, read only
    <module>/data/    defaults: *.yaml, then os/<family>/<release>.yaml
  modules.yaml        the modules of the workspace and where they come from
  facts/              what suil last read on each node, written by suil
  .runs/              the resolved configuration of each run, written by suil
```

The layout under `data/` other than `common.yaml` is not fixed: it is whatever
the `hierarchy` in `common.yaml` names. The tree above follows the default
hierarchy. The smallest workspace that runs is `common.yaml`, one role file
and one node file:

```yaml
# data/common.yaml
deployment:
  ssh_port:                 22
  ssh_user:                 deploy
  ssh_accept_unknown_hosts: yes

hierarchy:
  - os/{family}/{release}.yaml
  - modules/{module}.yaml
  - roles/{role}.yaml
  - nodes/{node}.yaml
```

```yaml
# data/roles/web.yaml
modules:
  - base
  - nginx
```

```yaml
# data/nodes/web-01.example.com.yaml
role: web

deployment:
  ssh_host: 192.0.2.10
```

### Common

`data/common.yaml` holds two keys.

- `deployment` - how suil connects to every node. Each key goes to the
  [pyinfra](https://pyinfra.com) SSH connector as host data. `ssh_host` is the
  address and defaults to the node name, `ssh_accept_unknown_hosts` turns
  into `ssh_strict_host_key_checking`. A role or a node overrides any of them
  in its own `deployment` key.
- `hierarchy` - the ordered list of layer patterns, lowest first. A pattern
  is a path under `data/` with placeholders: `{family}` and `{release}` from
  the OS of the node, `{module}` for each module of the node, `{role}` and
  `{node}`.

The pattern with `{role}` is where suil looks for roles, the pattern with
`{node}` is where it looks for nodes. Both must be in the hierarchy.

### Hierarchy

Suil builds the configuration of every node of a run the same way.

1. It reads the node file. The file must exist, and its `role` names the
   role of the node.
2. It reads the role file, which must exist too. The modules of the node are
   the role's `modules` followed by the node's own `modules`, without
   duplicates.
3. When the OS of the node is known, the modules are put in run order: every
   module after the modules its `requires.yaml` names, depth first, in the
   order of each list. A cycle is an error.
4. It merges the layers, each one over the previous: `deployment` from
   `common.yaml`, the `data/*.yaml` of every module followed by that
   module's own `data/os/{family}/{release}.yaml`, then every hierarchy
   pattern in order. A pattern with `{module}` is read once per module.
5. It expands the lookups, see [Lookup](#lookup).

Every top-level key of the result is a module name: `ssh:` in any layer is the
configuration of the `ssh` module. A missing layer file is an empty layer,
except the node file and the role file.

Dicts merge key by key and lists concatenate. A tag on a value changes that
for the value:

| Tag | Effect |
| --- | ------ |
| `!replace` | Replaces the value below instead of merging with it |
| `!append` | Concatenates a list, the default made explicit |
| `!merge` | Merges a list of dicts item by item, matched by `name` |
| `!delete` | Removes the key from the result |

```yaml
# data/nodes/web-01.example.com.yaml
example:
  packages: !replace
    - htop
```

The OS layer is the one only the node knows. Suil probes the OS when it
connects and caches the family and release in `facts/<node>/suil.yaml`. A node
with no cache is resolved without the OS layer, and its module list is marked
provisional until the run probes it.

### Secrets

A secret is stored encrypted in place, in any data file, as an `!ENC[...]`
value made with [age](https://age-encryption.org):

```bash
suil encrypt 'the value'
```

Suil keeps the ciphertext while it resolves the data. It decrypts a secret
only while it applies the node that uses it, with the key in `SUIL_AGE_KEY`.
Everything that is printed, written to `.runs/` or sent to a node for fact
collection carries a `sha256:` digest in place of the secret.

### Lookup

`!LOOKUP` reads a field from the nodes of the run instead of repeating it in
the data. It takes these keys:

| Key | Meaning |
| --- | ------- |
| `field` | The dotted path to read on each node; required |
| `nodes` | A glob over node names; `*` by default |
| `role` | Only nodes of this role |
| `ip` | `v4`, `v6` or `any` (default); keeps addresses of that family |
| `format` | How each value is written, with `{value}`, `{node}` and `{role}`; `{value}` by default |
| `self` | `include` (default), `exclude` or `only` the node that asks |

Inside a list the values found are spliced in place, beside the literal items.
Anywhere else the marker becomes the list of values. The values are sorted by
node name, so a rendered file does not change between runs.

```yaml
# data/modules/unbound.yaml
unbound:
  local_zones:
    - name: example.com
      type: transparent
      data:
        - "gw.example.com. A 192.0.2.1"
        - !LOOKUP
          field:  unbound.host_address
          format: "{node}. A {value}"
```

A lookup sees only the nodes of the run, the way a
[Hiera](https://www.puppet.com/docs/puppet/latest/hiera_intro.html) lookup
sees only the data of the catalogue being compiled. A run for one role sees
the nodes of that role, and a run for one node sees that node alone. A
lookup that finds nothing fails the run with the node and the field. A node
whose field is missing or empty is skipped.

A lookup reads the other nodes as merged, before their own lookups are
expanded, so one lookup never reads another.

## Run

A run is one role or one node. Suil resolves every node of it into a
`Directory` before anything connects. The `Directory` does not change after
that, except for the OS layer each node gets when it is probed. Modules never
see it: a module gets its configuration, its facts and `force`.

### Commands

```bash
suil apply --role web
suil apply --role web --confirm
suil apply --node web-01.example.com --confirm --dry-run
suil config --role web
suil facts --node web-01.example.com
suil nodes
suil modules
suil init
suil --version
suil
```

- `apply` shows the nodes of the run and their modules. It applies them only
  with `--confirm`. `--dry-run` connects and shows what would change,
  changing nothing. `--force` runs every module even when nothing changed.
- `config` shows the run and the public configuration of every module,
  without connecting.
- `facts` connects, probes and collects facts, and changes nothing.
- `nodes` lists the nodes of the workspace and their roles. `modules` lists
  the modules, their `requires` and their run order.
- `validate` checks `modules.yaml` and every module it declares and connects
  to nothing; `config`, `facts` and `apply` run it first. `install` clones
  the Git repositories into the suil cache, and `autoupdate` moves each
  `version` to the newest tag.
- `init` lays out an empty workspace in the current directory:
  `data/common.yaml` with the default hierarchy, the layer directories
  under `data/` and `modules/`. `modules.yaml` is yours to write. It writes
  nothing where `data/`, `modules/` or `modules.yaml` already is.
- `--version` prints the version of the installed package.
- `suil` with no command opens the interactive mode. It asks for one role,
  shows the run and asks before it applies.

Give `--role` or `--node`, not both. The command line never asks a question:
`--confirm` is the only way to apply from it.

### Node by node

Suil applies the nodes of a run one after another. A node that fails stops
the run, and the nodes after it are not touched.

```text
connect      SSH to the node
probe        read the OS, cache it, resolve the node again with the OS layer
configs      validate every module configuration, decrypt its secrets
facts        every module's collector reads the node
queue        every module queues the operations that close its diff
apply        pyinfra runs the queue; --dry-run stops here
facts again  only for the modules that queued operations
check        module problems and a remaining diff fail the run
record       .runs/<timestamp>/<node>/ with the public configuration
```

A module queues operations only when its expected state differs from the
facts, or when `--force` is given or its code changed since the last run. A
node that already matches gets no operations. The record is written after the
node, also when the apply or the check failed.

### Settings

Suil reads its settings from the environment and from `.env` in the
workspace, when it starts:

| Variable | Purpose |
| -------- | ------- |
| `SUIL_AGE_KEY` | age private key; decrypts `!ENC[...]` values |
| `SUIL_AGE_RECIPIENT` | age public key; `suil encrypt` encrypts to it |
| `SUIL_SUDO_PASSWORD` | sudo password on the nodes |
| `SUIL_LOG_COLOR` | `false` turns colored output off |

A variable set in the environment wins over the same one in `.env`.
