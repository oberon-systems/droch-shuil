from suil.libs import module_diff_touches


def test_a_path_is_touched_by_itself_and_by_anything_below_it():
    diff = {('service', 'running'): {'expected': True, 'actual': False}}

    assert module_diff_touches(diff, 'service')
    assert module_diff_touches(diff, 'service', 'running')
    assert not module_diff_touches(diff, 'unit')


def test_an_empty_diff_touches_nothing_and_force_touches_everything():
    assert not module_diff_touches({}, 'service')
    assert module_diff_touches(None, 'service')
