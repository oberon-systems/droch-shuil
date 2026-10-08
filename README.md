# suil

suil provisions Linux hosts from declarative data, on top of
[pyinfra](https://pyinfra.com). A workspace holds the site data and declares
its modules in `modules.yaml`; suil resolves them into the configuration of
each node, collects facts, applies only what differs and checks that the node
converged.

## Install

```bash
pip install suil
```

## Development

```bash
make install
make test
make lint
make docs
```

`make install` creates `.venv`, installs the tooling from `requirements.txt`
and the pre-commit hooks. Commits go through commitizen: `cz commit`.

## Releases

A `vX.Y.Z` tag that matches the version in `pyproject.toml` builds the sdist
and the wheel and publishes them to [PyPI](https://pypi.org/project/suil/).
The documentation is rebuilt and published to GitHub Pages on every push to
`main` that changes `docs/`, `README.md` or `mkdocs.yml`.

## License

[MIT](LICENSE)
