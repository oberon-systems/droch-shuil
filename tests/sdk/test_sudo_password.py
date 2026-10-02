"""The sudo password has to be handed to a bare connector call.

An operation or a fact takes it out of Config through pop_global_arguments();
host.run_shell_command() and host.put_file() do not, and pyinfra then prompts
for it on the terminal in the middle of a run.
"""

from suil.sdk.libs.host import put_content, run_command, sudo_password


class Output:

    stdout = ''
    stderr = ''


class Host:

    def __init__(self, password):
        self.state = type('State', (), {'config': type('Config', (), {'SUDO_PASSWORD': password})})
        self.calls = []

    def run_shell_command(self, command, **arguments):
        self.calls.append(arguments)

        return True, Output()

    def put_file(self, source, destination, **arguments):
        self.calls.append(arguments)

        return True


def test_a_command_carries_the_password_of_the_run():
    host = Host('secret')
    run_command(host, 'true')

    assert host.calls[0]['_sudo'] is True
    assert host.calls[0]['_sudo_password'] == 'secret'


def test_an_upload_carries_it_too():
    host = Host('secret')
    put_content(host, 'content', '/tmp/staged')

    assert host.calls[0]['_sudo_password'] == 'secret'


def test_an_empty_password_is_no_password():
    # A cloud image sudo's with none at all, and '' would be sent as one.
    assert sudo_password(Host('')) is None


def test_a_host_with_no_state_is_not_an_error():
    assert sudo_password(object()) is None
