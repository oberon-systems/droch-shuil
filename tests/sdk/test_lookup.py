import pytest
import yaml

from suil.sdk.errors import DataError
from suil.sdk.libs import config, inventory
from suil.sdk.libs.yaml.load import SuilLoader
from suil.sdk.models import Lookup

VIEWS = {
    'b-01.example.com': {'role': 'gateway', 'resolver': {'host_address': '10.0.0.2'}},
    'a-01.example.com': {'role': 'gateway', 'resolver': {'host_address': '10.0.0.1'}},
    'c-01.other.net':   {'role': 'edge', 'resolver': {'host_address': ['10.0.0.3', 'fd00::3']}},
    'd-01.example.com': {'role': 'edge', 'resolver': {'host_address': ''}},
}


def lookup(**spec):
    spec.setdefault('field', 'resolver.host_address')

    return Lookup(spec)


def test_a_lookup_reads_every_node_sorted_by_key():
    assert inventory.lookup(lookup(format='{node}. A {value}'), VIEWS) == [
        'a-01.example.com. A 10.0.0.1',
        'b-01.example.com. A 10.0.0.2',
        'c-01.other.net. A 10.0.0.3',
        'c-01.other.net. A fd00::3',
    ]


def test_a_node_without_the_field_is_skipped_rather_than_failing():
    assert 'd-01.example.com' not in ''.join(inventory.lookup(lookup(format='{node}'), VIEWS))


def test_nodes_and_role_narrow_the_match():
    assert inventory.lookup(lookup(nodes='*.example.com', format='{node}'), VIEWS) == [
        'a-01.example.com', 'b-01.example.com']
    assert inventory.lookup(lookup(role='edge', ip='v4', format='{node}'), VIEWS) == [
        'c-01.other.net']


def test_self_include_exclude_and_only():
    # ip: v4 keeps one value per node, so the list is one entry per name.
    names = lookup(ip='v4', format='{node}')

    assert inventory.lookup(names, VIEWS, 'a-01.example.com')[0] == 'a-01.example.com'
    assert inventory.lookup(lookup(ip='v4', format='{node}', **{'self': 'exclude'}),
                            VIEWS, 'a-01.example.com') == [
        'b-01.example.com', 'c-01.other.net']
    assert inventory.lookup(lookup(ip='v4', format='{node}', **{'self': 'only'}),
                            VIEWS, 'a-01.example.com') == ['a-01.example.com']


def test_the_ip_filter_splits_the_families():
    assert inventory.lookup(lookup(ip='v6'), VIEWS) == ['fd00::3']
    assert inventory.lookup(lookup(ip='v4'), VIEWS) == ['10.0.0.1', '10.0.0.2', '10.0.0.3']


def test_a_marker_in_a_list_splices_beside_the_literals():
    data = {'data': ['gw.example.com. A 10.9.9.9', lookup(format='{node}. A {value}')]}

    assert config.expand_lookups(data, VIEWS, None)['data'] == [
        'gw.example.com. A 10.9.9.9',
        'a-01.example.com. A 10.0.0.1',
        'b-01.example.com. A 10.0.0.2',
        'c-01.other.net. A 10.0.0.3',
        'c-01.other.net. A fd00::3',
    ]


def test_a_marker_outside_a_list_becomes_the_list_of_values():
    assert config.expand_lookups({'addresses': lookup(ip='v4')}, VIEWS, None) == {
        'addresses': ['10.0.0.1', '10.0.0.2', '10.0.0.3']}


def test_a_lookup_that_finds_nothing_in_the_run_fails():
    with pytest.raises(DataError):
        config.expand_lookups({'addresses': lookup(role='nowhere')}, VIEWS, 'a-01.example.com')


def test_the_tag_parses_out_of_yaml():
    data = yaml.load('records:\n  - !LOOKUP\n    field: resolver.host_address\n',
                     Loader=SuilLoader)

    assert data['records'][0] == lookup()


def test_an_unknown_key_or_a_missing_field_is_refused():
    with pytest.raises(DataError):
        Lookup({'field': 'a.b', 'nope': 1})

    with pytest.raises(DataError):
        Lookup({'nodes': '*'})

    with pytest.raises(DataError):
        Lookup({'field': 'a.b', 'ip': 'v5'})
