import os
import subprocess

from importlib.metadata import version

import click
import pytest

from click.testing import CliRunner

from suil import completion
from suil.cli import main
from tests.test_workspace import tree


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.delenv('XDG_DATA_HOME', raising=False)
    monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)


def offered(script, workspace, *words, path=os.environ['PATH']):
    line = ' '.join(f'"{word}"' for word in words)
    run = f'source {script}; COMP_WORDS=(suil {line}); COMP_CWORD={len(words)}; _suil; echo "${{COMPREPLY[*]}}"'
    env = {**os.environ, 'PATH': path}

    return subprocess.run(['bash', '-c', run], cwd=workspace, env=env, capture_output=True, text=True,
                          check=True).stdout.split()


@pytest.mark.parametrize('shell', completion.SHELLS)
def test_the_script_carries_every_command_and_option_and_the_version(shell):
    script = completion.source(main, shell)

    assert completion.stamp() in script.splitlines()[:2]
    assert 'python' not in script and '_SUIL_COMPLETE' not in script
    assert '--help' not in script and '--version' not in script and 'help' in script and 'version' in script

    for name, command in main.commands.items():
        assert name in script
        assert all(opt[2:] in script for param in command.params if isinstance(param, click.Option)
                   for opt in param.opts)


def test_bash_tab_offers_the_commands_options_roles_and_nodes(tmp_path):
    tree(tmp_path, 'alpha-01.example.com', 'a')
    script = completion.install(main, 'bash')

    assert 'completion' in offered(script, tmp_path, '')
    assert offered(script, tmp_path, 'apply', '--d') == ['--dry-run']
    assert offered(script, tmp_path, 'apply', '--role', '') == ['web']
    assert offered(script, tmp_path, 'facts', '--node', 'al') == ['alpha-01.example.com']
    assert offered(script, tmp_path / 'home', 'apply', '--role', '') == []


def test_completion_installs_where_the_shell_loads_it(tmp_path):
    result = CliRunner().invoke(main, ['completion', 'bash'])

    assert result.exit_code == 0
    assert completion.stamp() in (tmp_path / 'home/.local/share/bash-completion/completions/suil').read_text()


def test_bash_script_rewrites_itself_only_when_suil_version_names_another_one(tmp_path):
    script = completion.install(main, 'bash')
    (tmp_path / 'bin').mkdir()
    (tmp_path / 'v').write_text(version('droch-shuil'))
    suil = tmp_path / 'bin' / 'suil'
    suil.write_text(f"""#!/bin/sh
[ "$1" = version ] && echo "suil, version $(cat {tmp_path / 'v'})" && exit
printf '_suil() {{ COMPREPLY=(rewritten); }}\\n' > {script}
""")
    suil.chmod(0o755)
    path = f"{tmp_path / 'bin'}:{os.environ['PATH']}"

    assert 'completion' in offered(script, tmp_path, '', path=path)

    (tmp_path / 'v').write_text('0.0.1')
    assert offered(script, tmp_path, '', path=path) == ['rewritten']


def test_completion_refuses_a_shell_it_cannot_tell(monkeypatch):
    monkeypatch.setenv('SHELL', '/bin/tcsh')

    assert CliRunner().invoke(main, ['completion']).exit_code == 2


def test_help_and_version_are_commands_and_no_flags():
    assert CliRunner().invoke(main, ['--help']).exit_code == 2
    assert CliRunner().invoke(main, ['--version']).exit_code == 2
    assert CliRunner().invoke(main, ['apply', '--help']).exit_code == 2
    assert 'Usage: suil apply' in CliRunner().invoke(main, ['help', 'apply'], prog_name='suil').output
    assert 'Usage: suil' in CliRunner().invoke(main, ['help'], prog_name='suil').output
    assert CliRunner().invoke(main, ['version']).output.startswith('suil, version ')
