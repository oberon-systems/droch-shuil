# Suil SDK

Modules get one supported import surface, `suil.sdk`: the models, three
interfaces with their protocols, the libs and the errors. A module is built on
them, and everything outside `suil.sdk` is private to suil. That is what makes
the later split into separate repositories possible.

- [Layout](#layout)
- [Interfaces](#interfaces)
- [Protocols](#protocols)
- [Secrets](#secrets)
- [Libs and errors](#libs-and-errors)
- [Examples](#examples)
- [Migration](#migration)
- [Acceptance](#acceptance)

## Layout

```text
suil/sdk/
  __init__.py       the import surface and SDK_VERSION
  models/           Context, Config, Secret, Encrypted, Tagged, Lookup
  protocols.py      Deploys, Expects, Checks, DeclaresFiles, Collects
  module.py         Module
  facter.py         Facter and the bootstrap that runs it on the node
  errors.py         Error and its subclasses
  libs/<kind>/      one function per file, by kind
```

The SDK is models, interfaces, protocols and libs, and nothing else. How a
module works inside is its own business: suil is a deployer and does not
decide what a module writes or where. The order of its operations, its
rendering and its restart conditions belong to the module.

## Interfaces

A module implements up to three interfaces, one subclass per file:
`Config` in `code/config.py`, `Module` in `code/main.py` and `Facter` in
`facts/collector.py`. A module with no code is a meta module, as `base` is,
and implements none.

### Config

`Config` is a [pydantic](https://docs.pydantic.dev) v2 model with
`extra='forbid'`, so a key the model does not know fails validation in any
data layer. `get_config` fills `suil`, a `Context` with `node`, `role`,
`family`, `release` and `ssh_user`, and validates the rest from the merged
data.

### Module

`Module` is generic over its `Config`. `Module(config)` is built once per node
with the validated config. Its methods:

- `deploy(facts, force)` - queue the operations that close the diff;
  mandatory.
- `expected()` - the state the facts must match; mandatory.
- `check(facts)` - problems judged from the facts; empty by default.
- `files()` - `{path: content | None}` for every file the module puts on the
  node, `None` for one that must go; empty by default.

The constructor attaches every function of `libs/module/` to the instance
under its own name, so a module calls `self.diff_configs(...)` or
`self.file_needs_write(...)` without importing them. The module writes its
files itself and gates each write with `file_needs_write`. Their digests stay
in `expected()`.

`load_class` imports `code/main.py` and returns its one `Module` subclass, or
`None` for a meta module. It refuses a file with none or several, a class that
does not override `deploy` or `expected`, and a method whose signature differs
from its protocol's.

### Facter

`Facter` is the only code that reads the node, so it runs there on the
standard library alone. Its `config` is the public config without `suil`. It
carries `read(path)`, `run(argv)` and `digest(value)`, which returns the same
`sha256:` form a `Secret` has in the public view.

`check_facter` checks `facts/collector.py` statically with `ast`, without
importing it: standard library imports and `from suil.sdk import Facter`
only, exactly one `Facter` subclass, and `collect()` with the protocol's
signature. `collect_facts` uploads `suil/sdk/facter.py`, the collector and the
public config, then runs the bootstrap with sudo. The bootstrap stands in for
`suil.sdk`, builds the one `Facter` with the config and prints the JSON of
`collect()`. `collect_facts` adds the digests of `files()` under `files`.

## Protocols

Every method of an interface is a `typing.Protocol`, and `load_class` compares
signatures against them:

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
    def files(self) -> dict[str, str | bytes | None]: ...

@runtime_checkable
class Collects(Protocol):
    def collect(self) -> dict: ...
```

`Config` has no protocol: its contract is the pydantic model. `Module` is
`Deploys` and `Expects`, with `Checks` and `DeclaresFiles` optional. `Facter`
is `Collects`, checked from the source because it is never imported on the
control machine.

## Secrets

`Encrypted` is an `!ENC[...]` value as the data loader reads it: its string is
the ciphertext, and `reveal()` decrypts it with `SUIL_AGE_KEY`. `get_config`
reveals every `Encrypted` of the node into a `Secret`, a `str` that holds the
plaintext, and hands that to the model.

A secret field is typed `Secret`. A field of its own turns any string into a
`Secret`, and in a union such as `dict[str, Secret | str]` a value stays a
`Secret` only when it arrived as one. The public view is the dump with
`context={'public': True}`, which writes every `Secret` as
`sha256:<hex of the plaintext>`; `get_public` and `strip_secrets` build it.
Under `strict=True` a `Secret` field takes only a `Secret` instance.

A plain `str` field would turn a `Secret` back into a plain string and leak
it into the public view. `get_config` refuses that: when a revealed plaintext
survives in the public view, it raises `ModuleConfigError` with the dotted
path of the field.

## Libs and errors

`suil.sdk.libs` holds one function per file, one directory per kind:
`config`, `host`, `inventory`, `merge`, `module`, `node`, `pyinfra`, `role`,
`run`, `string` and `yaml`. A name does not repeat its location:
`libs.module.diff_configs`, not `module_diff_configs`. The kinds are exported
as modules, because `collect` exists in both `node` and `role`.

`suil.sdk.errors` holds `Error`, which logs itself when it is constructed,
and `DataError`, `ModuleError`, `ModuleConfigError`, `ModuleOrderError`,
`ModuleValidateError`, `SecretError`, `NodeProbeError` and `DeploymentError`.
Raise one and never log it as well.

## Examples

A module's config with a secret field:

```python
from suil.sdk import Config, Secret


class Config(Config):
    password: Secret
    env:      dict[str, Secret | str] = {}
```

A module that gates its one file on the facts:

```python
from io import StringIO

from pyinfra.operations import files

from suil.sdk import Module

PATH = '/etc/demo.conf'


class Demo(Module):

    def deploy(self, facts: dict, force: bool) -> None:
        content = self.files()[PATH]

        if self.file_needs_write(facts, PATH, content, force):
            files.put(name=f'write {PATH}', src=StringIO(content), dest=PATH)

    def expected(self) -> dict:
        return {'files': {PATH: self.file_digest(self.files()[PATH])}}

    def files(self) -> dict[str, str | bytes | None]:
        return {PATH: f'node {self.config.suil.node}\n'}
```

A collector:

```python
from suil.sdk import Facter


class Demo(Facter):

    def collect(self) -> dict:
        return {'hostname': self.read('/etc/hostname')}
```

## Migration

The SDK is built and tested beside `suil/libs/`, `suil/models.py` and the
modules, which are not edited until the runner moves. Then:

- the runner calls `get_config`, `load_class`, `check_facter`, `get_public`
  and the `run_*` libs of `suil.sdk`, and `errors_handler` treats
  `suil.sdk.errors.Error` as its own;
- every module moves in one commit: free functions become methods of its
  `Module`, the collector becomes a `Facter`, secret fields become `Secret`;
- `suil/libs/`, `suil/models.py`, `suil/module.py` and their tests are
  deleted.

Behaviour on hosts does not change: the same config queues the same
operations.

## Acceptance

- Every module implements its interfaces and imports suil only through
  `suil.sdk` and `suil.testing`.
- A module whose class misses a mandatory method, or has a method with the
  wrong signature, is refused at load with the module, the file and the
  expected signature.
- A collector that imports more than the standard library and `Facter` is
  refused before it is uploaded.
- The public view of every node is identical to the one built by value
  before, and an `!ENC` value in a field not typed `Secret` fails the config.
