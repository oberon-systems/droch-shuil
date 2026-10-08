from .file_digest import file_digest


def file_needs_write(facts: dict, path: str, content: str | bytes | None, force: bool = False) -> bool:
    """Whether the file the module would put at `path` differs from the one the facts record.

    None content means the file must not be there, so a recorded file is a write too.
    """
    recorded = (facts.get('files') or {}).get(path)

    if content is None:
        return force or recorded is not None

    return force or recorded != file_digest(content)
