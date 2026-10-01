"""Base of every module's facts/collector.py. It runs on the node: standard library only."""

import hashlib
import subprocess


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
