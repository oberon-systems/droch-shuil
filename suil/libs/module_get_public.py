from suil.models import Secret


def module_get_public(module: str, node, config, age_key: str | None) -> dict:
    """The validated config as it may be written down: every secret a digest.

    The masking is done by value rather than by walking the model, because
    pydantic coerces Secret to a plain str during validation - by the time the
    config exists, nothing on it is recognisable as a secret any more.
    """
    digests = {}
    _collect(getattr(node, module, None) or {}, digests, age_key)

    data = config if isinstance(config, dict) else config.model_dump(mode='json')

    return _mask(data, digests)


def _collect(data, digests: dict, key: str | None) -> None:
    if isinstance(data, Secret):
        digests[data.reveal(key)] = data.digest()

    elif isinstance(data, dict):
        for value in data.values():
            _collect(value, digests, key)

    elif isinstance(data, list):
        for value in data:
            _collect(value, digests, key)


def _mask(data, digests: dict):
    if isinstance(data, str):
        return digests.get(data, data)

    if isinstance(data, dict):
        return {key: _mask(value, digests) for key, value in data.items()}

    if isinstance(data, list):
        return [_mask(value, digests) for value in data]

    return data
