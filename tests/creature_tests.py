from nose.tools import assert_equals
from rise_gen.creature import Creature
from rise_gen.dice import Die, DieCollection

def setup():
    pass

def teardown():
    pass

def test_fighter_properties():
    c = Creature.from_sample_creature('fighter')
    correct_properties = {
        'accuracy': 8,
        'armor_check_penalty': 3,
        'armor_defense': 21,
        'attack_count': 1,
        'combat_prowess': 3,
        'damage_bonus': 2,
        'damage_dice': DieCollection(Die(8)),
        'fortitude': 20,
        'hit_points': 10,
        'maneuver_defense': 14,
        'mental': 13,
        'name': 'fighter',
        'reach': 5,
        'reflex': 10,
        'space': 5,
        'speed': 30,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equals(getattr(c, key), correct_properties[key])

def test_fighter_properties_at_higher_level():
    c = Creature.from_sample_creature('fighter', level=10)
    correct_properties = {
        'accuracy': 18,
        'armor_check_penalty': 3,
        'armor_defense': 30,
        'attack_count': 3,
        'combat_prowess': 12,
        'damage_bonus': 12,
        'damage_dice': DieCollection(Die(8)),
        'fortitude': 33,
        'hit_points': 160,
        'maneuver_defense': 23,
        'mental': 23,
        'name': 'fighter',
        'reach': 5,
        'reflex': 17,
        'space': 5,
        'speed': 30,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equals(getattr(c, key), correct_properties[key])
