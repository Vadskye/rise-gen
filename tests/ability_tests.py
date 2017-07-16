from nose.tools import assert_equals
from rise_gen.abilities.ability import Ability


class SampleCreature:
    def __init__(self):
        self.name = 'sample creature'
        self.level = 0
        self.levels = dict()


def setup():
    pass


def teardown():
    pass


def test_ability_prerequisites():
    sc = SampleCreature()
    a = Ability.by_name('fast movement')

    # check when prerequisites are not met
    speed = 20
    if a.prerequisite(sc):
        # apply the effects of the fast movement ability
        speed = a.effects[0](sc, speed)
    assert_equals(speed, 20)

    # check when prerequisites are met
    speed = 20
    sc.levels['barbarian'] = 2
    if a.prerequisite(sc):
        # apply the effects of the fast movement ability
        speed = a.effects[0](sc, speed)
    assert_equals(speed, 30)
