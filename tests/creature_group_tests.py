from nose.tools import assert_equal, assert_true
from rise_gen.creature import Creature
from rise_gen.creature_group import CreatureGroup

def setup():
    pass

def teardown():
    pass

def test_creature_group_init():
    fighter = Creature.from_sample_creature('fighter', level=1)
    group = CreatureGroup([fighter])

    assert_equal(group.get_living_creature(), fighter)
    assert_true(group.is_alive())

def test_accuracy():
    fighter = Creature.from_sample_creature('fighter', level=1)
    fighter_group = CreatureGroup([fighter])

    # Use a technically different Creature
    fighter2 = Creature.from_sample_creature('fighter', level=1)
    fighter_group2 = CreatureGroup([fighter2])

    # TODO: make this deterministic
    assert_equal(fighter_group.get_accuracy(fighter_group2, 1), 0)
