from pathlib import Path


def module_get_names(modules_dir: Path) -> list[str]:
    if not Path(modules_dir).is_dir():
        return []

    return sorted(entry.name for entry in Path(modules_dir).iterdir() if entry.is_dir())
