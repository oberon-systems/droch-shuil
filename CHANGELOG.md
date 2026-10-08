## v0.3.0 (2026-10-08)

### Features

- **suil**: validate module imports and host reads

## v0.2.0 (2026-10-08)

### Features

- **suil**: declare modules in modules.yaml, add install, autoupdate and validate
- **tests**: guard modules to import suil only through suil.sdk and suil.testing
- **sdk**: test the sdk: loader, facter, imports, packaging, ported libs tests
- **sdk**: copy the errors into suil.sdk.errors, base class Error
- **sdk**: hand the model Secret values, build the public view from them
- **sdk**: run the collector through the Facter bootstrap, check it with ast
- **sdk**: add load_class, the loader of the one Module subclass of code/main.py
- **sdk**: add suil.sdk: models, protocols, Module, Facter, libs by kind
- **suil**: errors_handler catches every error of the run
- **suil**: log lines carry their level, continuations and tracebacks indented
- **suil**: draft module and collector interface
- **repos**: declare repositories in data and read a private s3 bucket
- **unbound**: module ported from the ansible role
- **suil**: inventory lookups through the !LOOKUP tag
- **suil**: brief without ssh, facts every run, diff-driven gate
- **suil**: secrets stay digests, diff reaches modules, failures readable
- **suil**: added deployment
- **suil**: directory and deployments impovements

### Bug Fixes

- **suil**: fail the run when facts still differ from expected()
- **suil**: record file digests in the facts, decide writes against them
- **suil**: force on a changed module, fail the run on what is not up
- **suil**: runner passes modules only config and facts, builds no diff
- **suil**: fail on a data key left without a value
- **tests**: build the run directory fixture out of public
- **suil**: keep the run directory to the public view
- **tests**: call packages _names with the argument it takes
- **suil**: hand the sudo password to direct connector calls
- **accounts**: ensure instead of state, no shape checks, narrows to the diff
- **suil**: deployment fixes

### Refactor

- **suil**: drop suil.libs and suil.models, the sdk is the only path
- **base**: test through suil.testing
- **docker**: move onto suil.sdk
- **awg-keeper**: move onto suil.sdk
- **amneziawg**: move onto suil.sdk
- **xray**: move onto suil.sdk
- **nginx**: move onto suil.sdk
- **nftables**: move onto suil.sdk
- **unbound**: move onto suil.sdk
- **repos**: move onto suil.sdk
- **accounts**: move onto suil.sdk
- **ssh**: move onto suil.sdk
- **packages**: move onto suil.sdk
- **selinux**: move onto suil.sdk
- **hostname**: move onto suil.sdk
- **suil**: run the runner on suil.sdk, old paths kept for pending modules
- **suil**: get_order and get_requires in suil.testing, drop the unused suil/module.py
- **sdk**: call Module methods from run_code, run_check, run_drift, get_files
- **suil**: Directory is the run, Deployment applies it node by node
- **tests**: module tests move into the modules they cover
- **pyinfra**: initial commits for runner

### Build

- **suil**: configure cz bump
- **suil**: publish as droch-shuil, with suil and droch-shuil commands
- **deps**: Bump commitizen from 4.19.0 to 4.19.1 in the pip group
- **suil**: package for PyPI as 0.2.0, tests beside the package
- **suil**: import the runner with its history
- **suil**: package suil.sdk and its subpackages
- **repo**: create new structure
- **repo**: initial tooling, PyPI publish and GitHub Pages docs

### Documentation

- **docs**: point the urls at droch-shuil, add the eye logo
- **suil**: match the workspace doc to the code, fix a 05 heading
- **suil**: record the sdk migration as landed
- **prompts**: close 03, the sdk migration becomes step 04, 04-06 move to 05-07
- **sdk**: rewrite 03-sdk.md to the code, record the sdk as done
- **suil**: info.md on the data layer, lookups and runs
- **suil**: design docs and execution prompts for the extraction
