# Migrating onto the SDK

The runner and every module move onto `suil.sdk`, which
[03-sdk.md](03-sdk.md) specifies. Afterwards `suil/libs/` and
`suil/models.py` are gone, and a module imports suil only through `suil.sdk`
and `suil.testing`. Behaviour on hosts does not change: the same config
queues the same operations.

- [Today](#today)
- [Runner](#runner)
- [Modules](#modules)
- [Removal](#removal)
- [Acceptance](#acceptance)

## Today

- `suil/cli.py`, `suil/deployment.py`, `suil/directory.py` and
  `suil/testing.py` import `suil.libs` and `suil.models`.
- The runner calls the free functions of a module by name:
  `module_run_code` (`deploy`), `module_run_drift` (`expected`),
  `module_run_check` (`check`) and `module_get_files` (`managed_files`).
- `module_get_public` masks secrets by value.
- `errors_handler` in `suil/errors.py` knows only `SuilError`, so it logs an
  sdk `Error` a second time, with a traceback.
- Every module with code imports `suil.libs`, `suil.models` or
  `suil.errors`, and is listed in `PENDING` of
  `suil/tests/test_modules_import_sdk.py`.

## Runner

The runner takes everything from `suil.sdk`:

- `get_config` for the model and `get_public` for the public view;
- `load_class` and `check_facter` before anything connects, and one
  `Module(config)` per node and module;
- `run_code`, `run_drift`, `run_check` and `get_files` on that instance, and
  `collect_facts` through the `Facter` bootstrap.

A module still in `PENDING` keeps running through the old paths: its free
functions and its collector as a script. `errors_handler` treats
`suil.sdk.errors.Error` as its own, and `suil.testing` loads modules through
`suil.sdk`.

## Modules

Every module moves in one commit:

- the free functions of `code/main.py` become methods of its one `Module`,
  and `managed_files()` becomes `files()`;
- `code/config.py` subclasses `suil.sdk.Config`, and every secret field is
  typed `Secret`;
- `facts/collector.py` becomes one `Facter` subclass;
- the tests import only `suil.sdk` and `suil.testing`, which gives them
  `get_order` and `get_requires`;
- the module leaves `PENDING`.

`test_modules_import_sdk.py` holds the line meanwhile: it fails on a module
outside `PENDING` that imports more, and on a module in `PENDING` that no
longer does.

## Removal

Once `PENDING` is empty, the old paths of the runner, `suil/libs/`,
`suil/models.py` and the tests in `suil/tests/` that `suil/tests/sdk/` copies
are deleted, and with them `PENDING` itself.

## Acceptance

- Every module implements its interfaces and imports suil only through
  `suil.sdk` and `suil.testing`.
- `suil apply --dry-run` for a full role queues the same operations as
  before.
- The public view of every node in `.runs/` is identical to the one built by
  value before.
