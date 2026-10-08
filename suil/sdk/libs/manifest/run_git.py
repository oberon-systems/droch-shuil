import os
import subprocess


def run_git(*args: str) -> subprocess.CompletedProcess:
    """git with an argument list, no hooks and no prompt for credentials."""
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *args], capture_output=True, text=True,
                          env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
