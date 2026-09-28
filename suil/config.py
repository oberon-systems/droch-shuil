from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):

    model_config = SettingsConfigDict(env_prefix='SUIL_', env_file='.env')

    # age keys, X25519. The private half decrypts, the public half encrypts.
    age_key:       str | None = None
    age_recipient: str | None = None

    # Sudo on the targets. Set it and pyinfra never prompts, mid-run or at all.
    sudo_password: str | None = None

    # Terminal output
    log_color: bool = True
