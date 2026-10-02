"""Base of every module's facts/collector.py. It runs on the node: standard library only.

Run as a script it is the bootstrap: python3 facter.py <collector> <config.json>.
"""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import types


class Facter:

    def __init__(self, config: dict) -> None:
        self.config = config

    def collect(self) -> dict:
        """What the node reports, as JSON-serialisable data."""
        raise NotImplementedError

    @staticmethod
    def read(path: str) -> str | None:
        try:
            with open(path) as stream:
                return stream.read()
        except OSError:
            return None

    @staticmethod
    def run(command: list[str]) -> tuple[int, str]:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        return result.returncode, result.stdout.decode().strip()

    @staticmethod
    def digest(value: str | None) -> str | None:
        return 'sha256:' + hashlib.sha256(value.encode()).hexdigest() if value else None


def main(collector: str, config: str) -> None:
    """Build the collector's one Facter with the public config and print the JSON of collect()."""
    for name in ('suil', 'suil.sdk'):
        sys.modules.setdefault(name, types.ModuleType(name))

    sys.modules['suil.sdk'].Facter = Facter

    loader = importlib.machinery.SourceFileLoader('collector', collector)
    code = importlib.util.module_from_spec(importlib.util.spec_from_loader('collector', loader))
    loader.exec_module(code)

    found = [
        value for value in vars(code).values()
        if isinstance(value, type) and issubclass(value, Facter) and value is not Facter
        and value.__module__ == code.__name__
    ]

    if len(found) != 1:
        sys.exit(f'{collector} must declare exactly one Facter subclass, found {len(found)}')

    with open(config) as stream:
        json.dump(found[0](json.load(stream)).collect(), sys.stdout)


if __name__ == '__main__':
    main(*sys.argv[1:])
