# suil

*suil* is the Irish and Scottish Gaelic word for eye or vision, and
*drochshuil* is the evil eye, the eye of the Fomorian king in the old myths.
The package is named after it.

suil provisions Linux hosts from declarative data, on top of
[pyinfra](https://pyinfra.com). A workspace holds the site data and declares
its modules in `modules.yaml`; suil resolves them into the configuration of
each node, collects facts, applies only what differs and checks that the node
converged.

## Install

```bash
pip install droch-shuil
```

The package is published as `droch-shuil` and imported as `suil`. It installs
the same command under two names, `suil` and `droch-shuil`.

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
and the wheel and publishes them to [PyPI](https://pypi.org/project/droch-shuil/).
The documentation is rebuilt and published to GitHub Pages on every push to
`main` that changes `docs/`, `README.md` or `mkdocs.yml`.

## License

[MIT](LICENSE)
