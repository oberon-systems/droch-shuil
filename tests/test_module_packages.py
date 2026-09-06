def config(load, suil_context, **kwargs):
    return load('packages', 'config').Config(suil=suil_context, **kwargs)


def test_a_bare_name_means_present(load, suil_context):
    entry = config(load, suil_context, list={'tmux': None})

    assert entry.list['tmux'].ensure == 'present'


def test_present_and_absent_go_into_separate_calls(load, suil_context):
    main = load('packages')
    entry = config(load, suil_context, list={
        'tmux': {'ensure': 'present'},
        'telnet': {'ensure': 'absent'},
    })

    assert main._names(entry, wanted=True) == ['tmux']
    assert main._names(entry, wanted=False) == ['telnet']


def test_a_version_is_appended_to_the_name_for_dnf(load, suil_context):
    main = load('packages')
    entry = config(load, suil_context, list={'net-tools': {'ensure': '2.10-8.el10'}})

    assert main._names(entry, wanted=True) == ['net-tools-2.10-8.el10']


def test_expected_is_the_config_shape_so_the_diff_compares_like_with_like(load, suil_context):
    main = load('packages')
    entry = config(load, suil_context, list={'tmux': None, 'telnet': {'ensure': 'absent'}})

    assert main.expected(entry) == {
        'list': {'tmux': {'ensure': 'present'}, 'telnet': {'ensure': 'absent'}}}
