from ...protocols import DeclaresFiles


def get_files(module: DeclaresFiles | None) -> dict:
    """The files the module puts on the host, path to content, None for a file that must go."""
    return dict(module.files()) if module else {}
