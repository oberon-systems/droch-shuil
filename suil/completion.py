import os

from importlib.metadata import version
from pathlib import Path

import click

SHELLS = ('bash', 'zsh', 'fish')
VALUES = {'role': 'roles', 'node': 'nodes'}


def detect_shell() -> str:
    return Path(os.environ.get('SHELL', '')).name


def stamp() -> str:
    return f"# suil {version('droch-shuil')}"


def target(shell: str) -> Path:
    data = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
    config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')

    return {
        'bash': data / 'bash-completion' / 'completions' / 'suil',
        'zsh':  Path.home() / '.zfunc' / '_suil',
        'fish': config / 'fish' / 'completions' / 'suil.fish',
    }[shell]


def install(group, shell: str) -> Path:
    path = target(shell)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source(group, shell))

    return path


def source(group, shell: str) -> str:
    """The script, rewritten by itself when it loads and the installed suil is not the version it was made by."""
    return {'bash': _bash, 'zsh': _zsh, 'fish': _fish}[shell](_tree(group), target(shell))


def _tree(group) -> dict:
    """Every command with its options, the options that take a workspace name, and its argument's choices."""
    tree = {'': {'options': [], 'names': {}, 'choices': sorted(group.commands)}}

    for name, command in sorted(group.commands.items()):
        options = [param for param in command.params if isinstance(param, click.Option)]
        tree[name] = {
            'options': [opt for param in options for opt in param.opts],
            'names': {opt: VALUES[param.name] for param in options if param.name in VALUES for opt in param.opts},
            'choices': [choice for param in command.params
                        if isinstance(param, click.Argument) and isinstance(param.type, click.Choice)
                        for choice in param.type.choices],
        }

    return tree


def _bash(tree, path) -> str:
    names = {opt: kind for item in tree.values() for opt, kind in item['names'].items()}
    cases = '\n'.join(f"            {name}) words='{' '.join(item['choices'] + item['options'])}' ;;"
                      for name, item in tree.items() if name)

    return f"""{stamp()}
_suil_names() {{
    local path
    for path in data/$1/*.yaml; do
        [[ -e $path ]] && basename "$path" .yaml
    done
}}

_suil() {{
    local cur=${{COMP_WORDS[COMP_CWORD]}} words=''

    case ${{COMP_WORDS[COMP_CWORD-1]}} in
{chr(10).join(f'        {opt}) words=$(_suil_names {kind}) ;;' for opt, kind in names.items())}
        *)
            if (( COMP_CWORD == 1 )); then
                words='{' '.join(tree['']['choices'] + tree['']['options'])}'
            else
                case ${{COMP_WORDS[1]}} in
{cases}
                esac
            fi ;;
    esac

    COMPREPLY=($(compgen -W "$words" -- "$cur"))
}}

_suil_found=$(suil version 2> /dev/null)

if [[ -n $_suil_found && ${{_suil_found##* }} != {version('droch-shuil')} ]] &&
        suil completion bash > /dev/null 2>&1; then
    source '{path}'
fi

unset _suil_found

complete -F _suil suil
"""


def _zsh(tree, path) -> str:
    names = {opt: kind for item in tree.values() for opt, kind in item['names'].items()}
    cases = '\n'.join(f"                {name}) candidates=({' '.join(item['choices'] + item['options'])}) ;;"
                      for name, item in tree.items() if name)

    return f"""#compdef suil
{stamp()}
_suil() {{
    local -a candidates

    case ${{words[CURRENT-1]}} in
{chr(10).join(f'        {opt}) candidates=(data/{kind}/*.yaml(N:t:r)) ;;' for opt, kind in names.items())}
        *)
            if (( CURRENT == 2 )); then
                candidates=({' '.join(tree['']['choices'] + tree['']['options'])})
            else
                case ${{words[2]}} in
{cases}
                esac
            fi ;;
    esac

    compadd -a candidates
}}

_suil_found=$(suil version 2> /dev/null)

if [[ -n $_suil_found && ${{_suil_found##* }} != {version('droch-shuil')} ]] &&
        suil completion zsh > /dev/null 2>&1; then
    source '{path}'
fi

unset _suil_found

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    _suil "$@"
else
    compdef _suil suil
fi
"""


def _fish(tree, path) -> str:
    lines = ['complete -c suil -f']

    for name, item in tree.items():
        when = '__fish_use_subcommand' if not name else f'__fish_seen_subcommand_from {name}'

        if item['choices']:
            lines.append(f"complete -c suil -n '{when}' -a '{' '.join(item['choices'])}'")

        for opt in item['options']:
            flag = f'-l {opt[2:]}' if opt.startswith('--') else f'-s {opt[1:]}'

            if kind := item['names'].get(opt):
                flag += f" -x -a '(for path in data/{kind}/*.yaml; basename $path .yaml; end)'"

            lines.append(f"complete -c suil -n '{when}' {flag}")

    body = ''.join(f'\n    {line}' for line in lines)

    return f"""{stamp()}
set -l found
command -q suil; and set found (suil version 2> /dev/null)

if test -n "$found"; and test (string split ' ' -- $found)[-1] != '{version('droch-shuil')}'
        and suil completion fish > /dev/null 2>&1
    source '{path}'
else{body}
end
"""
