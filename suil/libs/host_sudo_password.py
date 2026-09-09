def host_sudo_password(host) -> str | None:
    """The sudo password of the run, for a call that talks to the connector
    directly.

    An operation or a fact gets it from `Config` through pop_global_arguments();
    a bare host.run_shell_command() does not, and pyinfra then prompts for it on
    the terminal instead. Empty is not a password - see pyinfra_make_state().
    """
    state = getattr(host, 'state', None)
    config = getattr(state, 'config', None)

    return getattr(config, 'SUDO_PASSWORD', None) or None
