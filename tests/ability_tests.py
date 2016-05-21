from nose.tools import *
from rise_gen.ability import Ability

class SampleCreature:
    def __init__(self):
        self.level = 0

def setup():
    pass

def teardown():
    pass

def test_ability_prerequisites():
    sc = SampleCreature()
    a = Ability.by_name('fast movement')

    # check when prerequisites are not met
    value = 20
    if a.prerequisite(sc):
        value = a.effects[0](sc, value)
    assert_equals(value, 20)

    # check when prerequisites are met
    value = 20
    sc.level = 10
    if a.prerequisite(sc):
        value = a.effects[0](sc, value)
    assert_equals(value, 30)
