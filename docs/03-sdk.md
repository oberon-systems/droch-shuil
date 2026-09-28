# Suil SDK

Modules get one supported import surface, `suil.sdk`, and it consists of three
interfaces: `Module`, `Config` and `Facter`. A module is built on them, and the
runner accepts nothing else. Everything outside `suil.sdk` becomes private and
may change without breaking a module, which is what makes the later split into
separate repositories possible.

## Today

- Module code imports `SuilConfig` from `suil.models`, `ModuleError` and
  `ModuleValidateError` from `suil.errors`, and helpers straight from
  `suil.libs`: `module_diff_configs`, `module_diff_names`,
  `module_diff_touches`, `module_file_digest`, `module_file_needs_write`,
  `module_validate_file`, `module_get_defaults`, `deep_merge`,
  `deep_merge_unwrap`.
- Module tests also import `module_get_order` and `module_get_requires`.
- `suil/module.py` holds `ModuleInterface` and `FactCollectorInterface`, ABC
  mixins nothing uses. Their `deploy(config, facts)` and `collect(config)`
  do not match the contract the runner calls.
- Modules find their own `templates/` and `files/` through
  `Path(__file__).resolve().parent.parent`, and each builds its own Jinja
  environment.

## Design

- A module implements all three interfaces: its `Config` in `code/config.py`,
  its `Module` in `code/main.py`, its `Facter` in `facts/collector.py`. Each
  file declares exactly one subclass.
- Every function of an interface is a `typing.Protocol`. The interface is the
  set of protocols it is made of, and a module is checked against those
  protocols when it is loaded, before anything connects.
- The runner works only through the interfaces. It instantiates the module's
  classes and calls their methods; it never looks up a free function by name
  and never builds a diff.
- `suil.sdk` exports the three interfaces, their protocols, `File`,
  `SuilContext`, `Secret`, the module errors and `SDK_VERSION`, SemVer from
  `0.1.0`.
  Test helpers such as `module_get_order` go through `suil.testing`.

## Interfaces

### Config

`Config` is a [pydantic](https://docs.pydantic.dev) v2 base model with
`extra='forbid'`. The runner fills `suil`, a `SuilContext` with node, role,
family, release and ssh user, and validates the rest from the merged data.

A secret field is typed `Secret`, and inside the model it holds the
plaintext. The public view is built by suil, not by the module: suil replaces
every `Secret` field with its `sha256:` digest, by field, from the types,
instead of matching plaintext values after the fact.

### Module

`Module` is generic over its `Config`. The runner builds it once per node with
the validated config, `Module(config)`, and calls:

- `deploy(facts, force)` - queue the operations that close the diff.
- `expected()` - the state the facts must match.
- `check(facts)` - problems judged from the facts; optional.
- `files()` - the `File` resources the module declares; optional.

The base class carries what every module needs, as methods instead of free
helpers:

- `diff(facts)` - `expected()` against the facts, keyed by tuple paths.
- `touches(diff, *path)`, `names(diff, collection)` - narrowing a diff.
- `changed(path)` - whether suil queued a write or a removal of that file in
  this run, for a module that restarts a service after its config changed.
- `path(*parts)`, `render(template, **context)` - the module's own files and
  templates, resolved only inside the module root and rendered by one narrow
  Jinja environment.

## Resources

### File

A file on the node is a resource of suil, like `file` in
[Puppet](https://www.puppet.com/docs/puppet/latest/types/file.html). The
module declares what the file must be; suil reads it on the node, compares,
validates, writes and removes it. No module reads, digests or writes a file
itself.

`File` is a frozen record:

- `path` - the absolute path on the node.
- `ensure` - `present` or `absent`.
- `content` - the bytes or text of the file, usually from `render()`.
- `source` - a file under the module's `files/`, instead of `content`.
- `owner`, `group`, `mode`.
- `validate` - the node's own checker, `%s` where the staged path goes, as
  `sshd -t -f %s`. A file it rejects never reaches its path.

For every declared `File` suil reads the sha256, the owner, the group and the
mode on the node and records them under `files` in the facts, beside what the
`Facter` reports. Before `deploy()` suil queues the writes and the removals
where the recorded state differs from the declared one, or all of them under
force. After the run a file that still differs fails the run like any other
drift, so a module's `expected()` no longer carries file digests.

### Facter

`Facter` is the only code that reads the node. It runs there, so it and
`suil/sdk/facter.py`, which defines it, use the standard library only. The
runner uploads both files, builds the module's facter with the public config,
calls `collect()` and reads the JSON it returns.

The base class gives the facter `config`, the public config as a dict, and
the reads every collector repeats today: `read(path)`, `run(argv)` and
`digest(value)`, which returns the same `sha256:` form a `Secret` has in the
public view.

## Protocols

The structure of the SDK, as the loader checks it:

```python
@runtime_checkable
class Deploys(Protocol):
    def deploy(self, facts: dict, force: bool) -> None: ...

@runtime_checkable
class Expects(Protocol):
    def expected(self) -> dict: ...

@runtime_checkable
class Checks(Protocol):
    def check(self, facts: dict) -> list[str]: ...

@runtime_checkable
class DeclaresFiles(Protocol):
    def files(self) -> list[File]: ...

@runtime_checkable
class Collects(Protocol):
    def collect(self) -> dict: ...
```

- `Config` has no protocol: its contract is the pydantic model itself.
- `Module` is `Deploys` and `Expects`; `Checks` and `DeclaresFiles` are
  optional and have empty defaults in the base class.
- `Facter` is `Collects`.

`isinstance` against a runtime protocol sees only that a method exists, so the
loader also compares each method's signature with the protocol's and reports
the module, the file and the expected signature on a mismatch.

## Meta modules

A meta module has no code and implements no interface. It exists only to pull
other modules in through `requires.yaml`, as `base` does.

## Migration

Every module under `modules/` moves to the three interfaces in one step per
module: the free functions of `code/main.py` become methods of its `Module`,
`facts/collector.py` becomes a `Facter`, secret fields become `Secret`, and
`managed_files()` with its `files.put` operations becomes `files()` returning
`File` resources.
`suil/module.py` is deleted. Behaviour on hosts does not change: the same
config queues the same operations.

A guard test beside `suil/tests/test_modules_read_facts.py` fails when module
code or module tests import any `suil.*` name other than `suil.sdk` and
`suil.testing`.

## Acceptance

- Every module implements `Config`, `Module` and `Facter`, and imports suil
  only through `suil.sdk` and `suil.testing`.
- A module whose class misses a protocol, or has a method with the wrong
  signature, is refused at load with the module, the file and the expected
  signature.
- Rendering through `render()` is byte-for-byte what the module rendered
  before, proven by golden tests.
- The public view of every node is identical to the one built by value
  today.
- A `File` changed on the node is written back, one whose `validate` fails is
  not, and one declared `absent` is removed, proven in tests without a node.
