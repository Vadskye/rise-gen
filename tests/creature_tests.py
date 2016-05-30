from nose.tools import assert_equals
from rise_gen.creature import Creature
from rise_gen.dice import Die, DieCollection
import yaml

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
        'land_speed': 30,
        'name': 'fighter',
        'reach': 5,
        'reflex': 10,
        'space': 5,
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
        'land_speed': 30,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equals(getattr(c, key), correct_properties[key])

def test_fighter_string():
    c = Creature.from_sample_creature('fighter')
    assert_equals(str(c), """
human fighter 1
[HP] 10; [Defs] AD 21, MD 14; Fort 20, Ref 10, Ment 13
[Atk] 8: 1d8+2; [Prowess] 3
[Attr] 4 0 4 0 0 0
[Space] 5, [Reach] 5, [Speed] 30
[Abil] Armor Discipline (Resilience), Magic Items, Size Modifiers
    """.strip())

def test_all_samples():
    return
    test_strings = dict()
    with open('tests/creature_test_strings.yaml', 'r') as test_strings_file:
        test_strings = yaml.load(test_strings_file)

    # first check pcs
    # currently missing: paladin, spellwarped
    for sample_name in 'barbarian cleric druid fighter ranger rogue sorcerer wizard'.split():
        pc = Creature.from_sample_creature(sample_name)
        assert_equals(type(pc), Creature)
        assert_equals(str(pc), test_strings[sample_name].strip())

    # now check monsters
    for sample_name in 'aboleth angel arkite_caster arkite_grappler arkite_monk black_bear brown_bear demogorgon dummy planetar super_bear torvid troll_mech wee_bear'.split():
        monster = Creature.from_sample_creature(sample_name)
        assert_equals(type(monster), Creature)
        assert_equals(str(monster), test_strings[sample_name].strip())
