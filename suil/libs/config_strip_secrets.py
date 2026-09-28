from pydantic import BaseModel

from suil.models import Secret


def config_strip_secrets(data):
    """Replace every Secret with sha256:<hex of the plaintext>.

    Enough to notice that a secret changed, not enough to leak one - which is
    what lets the run catalogue and the facts be looked at and diffed.
    """
    if isinstance(data, Secret):
        return data.digest()

    # A module config arrives as its pydantic model, which yaml cannot represent.
    if isinstance(data, BaseModel):
        return config_strip_secrets(data.model_dump(mode='json'))

    if isinstance(data, dict):
        return {key: config_strip_secrets(value) for key, value in data.items()}

    if isinstance(data, list):
        return [config_strip_secrets(item) for item in data]

    return data


def config_reveal_secrets(data, key: str | None):
    """The other direction: hand a module the plaintext, in memory only."""
    if isinstance(data, Secret):
        return data.reveal(key)

    if isinstance(data, dict):
        return {name: config_reveal_secrets(value, key) for name, value in data.items()}

    if isinstance(data, list):
        return [config_reveal_secrets(item, key) for item in data]

    return data
