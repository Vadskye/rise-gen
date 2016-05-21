from nose.tools import *
from rise_gen.dice import Die

def setup():
    pass

def teardown():
    pass

def test_average():
    d = Die(6)
    assert_equal(d.average(), 3.5)

    d = Die(20)
    assert_equal(d.average(), 10.5)

    d = Die(6, 4)
    assert_equal(d.average(), 14)

def test_operations():
    d = Die(6) + 3
    assert_equal(d, Die(6, 2))

    d = Die(6, 4) - 2
    assert_equal(d, Die(8, 2))

def test_string_interpretation():
    d = Die.from_string('d8')
    assert_equal(d, Die(8))

    d = Die.from_string('3d6')
    assert_equal(d, Die(6, 3))
