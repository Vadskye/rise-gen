from nose.tools import assert_equal
from rise_gen.dice import DicePool

def setup():
    pass

def teardown():
    pass

def test_average():
    d = DicePool(6)
    assert_equal(d.average(), 3.5)

    d = DicePool(20)
    assert_equal(d.average(), 10.5)

    d = DicePool(6, 4)
    assert_equal(d.average(), 14)

def test_operations():
    d = DicePool(6) + 3
    assert_equal(d, DicePool(6, 2))

    d = DicePool(6, 4) - 2
    assert_equal(d, DicePool(8, 2))

def test_string_interpretation():
    d = DicePool.from_string('d8')
    assert_equal(d, DicePool(8))

    d = DicePool.from_string('3d6')
    assert_equal(d, DicePool(6, 3))
