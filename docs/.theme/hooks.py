"""MkDocs hooks: the README is the home page."""

import re
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\]\((?!https?://|#)([^)]+)\)")


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Serve README.md as index.md, its links pointed at the site or at GitHub."""
    blob = config.repo_url.rstrip("/") + "/blob/main/"

    def link(match: re.Match[str]) -> str:
        target = match.group(1)
        return f"]({target.removeprefix('docs/')})" if target.startswith("docs/") else f"]({blob}{target})"

    page = "---\ntitle: Home\n---\n\n" + LINK.sub(link, (ROOT / "README.md").read_text(encoding="utf-8"))
    home = File.generated(config, "index.md", content=page)
    # edit_uri is relative to docs/, and "Edit on GitHub" has to open the README.
    home.edit_uri = "../README.md"
    files.append(home)
    return files
