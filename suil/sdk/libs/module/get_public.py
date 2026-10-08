from ..config.strip_secrets import strip_secrets


def get_public(config) -> dict:
    """The validated config as it may be written down: every Secret field a digest."""
    return strip_secrets(config)
