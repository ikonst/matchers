from matchers import *

def test_diff():
    assert {
        'foo': 123,
        'bar': '456',
    } == {
        'foo': AnyInteger(),
        'bar': AnyOf(456, '789'),
    }