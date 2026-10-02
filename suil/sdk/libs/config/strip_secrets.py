from pydantic import BaseModel

from suil.sdk.models import Encrypted, Secret


def strip_secrets(data):
    """Replace every Encrypted and Secret with sha256:<hex of the plaintext>.

    Enough to notice that a secret changed, not enough to leak one - which is
    what lets the run catalogue and the facts be looked at and diffed.
    """
    if isinstance(data, Encrypted):
        return data.digest()

    if isinstance(data, Secret):
        return data.digest() if data else ''

    # A module config arrives as its pydantic model; its Secret fields digest themselves.
    if isinstance(data, BaseModel):
        return strip_secrets(data.model_dump(mode='json', context={'public': True}))

    if isinstance(data, dict):
        return {key: strip_secrets(value) for key, value in data.items()}

    if isinstance(data, list):
        return [strip_secrets(item) for item in data]

    return data


def reveal_secrets(data, key: str | None):
    """The other direction: hand a module the plaintext as a Secret, in memory only."""
    if isinstance(data, Encrypted):
        return Secret(data.reveal(key))

    if isinstance(data, dict):
        return {name: reveal_secrets(value, key) for name, value in data.items()}

    if isinstance(data, list):
        return [reveal_secrets(item, key) for item in data]

    return data
