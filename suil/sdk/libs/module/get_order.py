from pathlib import Path

from suil.sdk.errors import ModuleError, ModuleOrderError

from .get_requires import get_requires


def get_order(modules: list[str], modules_dir: Path) -> list[str]:
    """Depth-first post-order over `requires`, so a dependency lands before its
    dependant and the order inside a requires list is the order of the run."""
    ordered: list[str] = []
    done: set[str] = set()
    path: list[str] = []

    def visit(name: str) -> None:
        if name in done:
            return

        if name in path:
            cycle = ' -> '.join(path[path.index(name):] + [name])
            raise ModuleOrderError(f'requires form a cycle: {cycle}')

        if not (Path(modules_dir) / name).is_dir():
            through = f" (required by {path[-1]})" if path else ''
            raise ModuleError(f'module {name!r} is not in {modules_dir}{through}')

        path.append(name)

        for requirement in get_requires(name, modules_dir):
            visit(requirement)

        path.pop()
        done.add(name)
        ordered.append(name)

    for module in modules:
        visit(module)

    return ordered
