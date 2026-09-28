# Suil architecture

Suil provisions Linux hosts from declarative data. This document states the
principles it is built on and the technologies it uses.

## Technologies

- Python 3 - the runner and every module.
- [pyinfra](https://pyinfra.com) - agentless execution over SSH; modules
  queue operations, pyinfra applies them.
- [pydantic](https://docs.pydantic.dev) v2 and pydantic-settings - module
  config models with `extra='forbid'`; runner settings from `SUIL_*` and
  `.env`.
- [PyYAML](https://pyyaml.org) with custom tags - site data: `!ENC`,
  `!LOOKUP`, `!replace`, `!append`, `!merge`, `!delete`.
- [age](https://age-encryption.org) (X25519) - encryption of secrets inside
  the data.
- [Click](https://click.palletsprojects.com) - CLI and TUI.
- [pytest](https://pytest.org) - module tests; fixtures ship as a plugin
  through an entry point.

## Lifecycle

1. **Build the catalogue.** For every node suil resolves its role, the
   ordered list of its modules and the validated config of each module. The
   catalogue is built on the control machine from local data and is complete
   before anything is applied.
2. **Apply the catalogue.** Suil connects to every node, collects facts, and
   lets each module queue the operations that bring the node to its config.
   After the run the facts are collected again and must match what the
   modules expect.

## Principles

1. **Declarative state.** Data describes what a resource must be, not the
   steps to get there. A module compares that description with the node and
   brings the node to it.
2. **Only the diff is applied.** A module applies only what differs between
   its expected state and the facts. A node that already matches gets no
   operations, so a repeated run changes nothing.
3. **Data apart from code.** Modules hold the logic and are the same for
   every node. What makes nodes differ lives only in the data.
4. **Modular system.** Every concern - accounts, ssh, nftables, and so on -
   is a separate module with its own config model, defaults, collector and
   tests. A node is described by the set of modules it runs.
5. **Hierarchical data with lookups.** A node's config is merged from layers:
   module defaults, OS, module, role and node, the later layer winning. A
   lookup lets one node read a field of other nodes, for example the
   addresses of its peers.
6. **Push.** Everything runs from the control machine over SSH. Nothing is
   installed on the nodes and no agent runs there.
7. **Fact collection.** Before and after a run every module collects facts
   from the node with its own collector. The facts are what the module
   compares its expected state with, and the collector is the only code
   that reads the node.
8. **Inline encryption with age.** A secret is stored encrypted in place,
   inside the ordinary data files, as an `!ENC[...]` value. It is decrypted
   only in memory on the control machine, when a module needs it.
9. **Every run is saved, without secrets.** The resolved catalogue of each
   run is written to disk before it is applied. Every secret in it is
   replaced by its `sha256:` digest, so runs can be kept and compared.
10. **`requires` and pseudo-modules (collectors).** A module declares the
    modules it depends on in `requires`, which fixes the run order. A
    pseudo-module has no code and only collects other modules under one
    name, as `base` does.
