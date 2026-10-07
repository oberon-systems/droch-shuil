# Migrating onto the SDK

The runner and every module moved onto `suil.sdk`, which
[03-sdk.md](03-sdk.md) specifies. The old libs and models are gone, and a
module imports suil only through `suil.sdk` and `suil.testing`. Behaviour on
hosts did not change: the same config queues the same operations. This
document records the step; it has landed.

- [Before](#before)
- [Runner](#runner)
- [Modules](#modules)
- [Removal](#removal)
- [Acceptance](#acceptance)

## Before

- The runner and `suil/testing.py` imported a flat package of libs and a
  models file next to it.
- The runner called the free functions of a module by name: `deploy`,
  `expected`, `check` and the one that listed the module's files.
- The public view masked secrets by value.
- `errors_handler` in `suil/errors.py` knew only the runner's own base
  error, so it logged an sdk `Error` a second time, with a traceback.
- Every module with code imported those libs, models or errors, and was
  listed in `PENDING` of `suil/tests/test_modules_import_sdk.py`.

## Runner

The runner takes everything from `suil.sdk`:

- `get_config` for the model and `get_public` for the public view;
- `load_class` and `check_facter` before anything connects, and one
  `Module(config)` per node and module;
- `run_code`, `run_drift`, `run_check` and `get_files` on that instance, and
  `collect_facts` through the `Facter` bootstrap.

While the modules moved, one still in `PENDING` kept running through the old
paths: its free functions and its collector as a script. `errors_handler`
treats `suil.sdk.errors.Error` as its own, and `suil.testing` loads modules
through `suil.sdk`.

## Modules

Every module moved in one commit:

- the free functions of `code/main.py` became methods of its one `Module`,
  and the function that listed its files became `files()`;
- `code/config.py` subclasses `suil.sdk.Config`, and every secret field is
  typed `Secret`;
- `facts/collector.py` became one `Facter` subclass;
- the tests import only `suil.sdk` and `suil.testing`, which gives them
  `get_order` and `get_requires`;
- the module left `PENDING`.

`test_modules_import_sdk.py` held the line meanwhile: it failed on a module
outside `PENDING` that imported more, and on a module in `PENDING` that no
longer did. It still fails on any module that imports more.

## Removal

Once `PENDING` was empty, the old paths of the runner, the old libs and
models and the tests in `suil/tests/` that `suil/tests/sdk/` copies were
deleted, and with them `PENDING` itself.

## Acceptance

- Every module implements its interfaces and imports suil only through
  `suil.sdk` and `suil.testing`.
- `suil apply --dry-run` for a full role queues the same operations as
  before.
- The public view of every node in `.runs/` is identical to the one built by
  value before.
