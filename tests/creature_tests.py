from nose.tools import assert_equal, assert_true
from rise_gen.creature import Creature
from rise_gen.dice import Die, DieCollection
import yaml

def setup():
    pass

def teardown():
    pass

def test_fighter_properties():
    c = Creature.from_sample_creature('fighter', level=1)
    correct_properties = {
        'accuracy': 8,
        'encumbrance_penalty': 3,
        'armor_defense': 22,
        'attack_count': 1,
        'combat_prowess': 3,
        'damage_bonus': 3,
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
        assert_equal(getattr(c, key), correct_properties[key], 'Property {} is wrong'.format(key))

def test_fighter_properties_at_higher_level():
    c = Creature.from_sample_creature('fighter', level=10)
    correct_properties = {
        'accuracy': 18,
        'encumbrance_penalty': 3,
        'armor_defense': 31,
        'attack_count': 3,
        'combat_prowess': 12,
        'damage_bonus': 12,
        'damage_dice': DieCollection(Die(8)),
        'fortitude': 33,
        'hit_points': 160,
        'maneuver_defense': 23,
        'mental': 22,
        'name': 'fighter',
        'reach': 5,
        'reflex': 17,
        'space': 5,
        'land_speed': 30,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equal(getattr(c, key), correct_properties[key], 'Property {} is wrong'.format(key))

def test_fighter_string():
    c = Creature.from_sample_creature('fighter', level=1)
    assert_equal(str(c), """
human fighter Fighter 1
[HP] 10; [Defs] AD 22, MD 14; Fort 20, Ref 10, Ment 13
[Atk] 8: 1d8+3; [Prowess] 3
[Attr] 4 0 4 0 0 0
[Space] 5, [Reach] 5, [Speed] 30
[Abil] Armor Discipline (Resilience), Magic Items, Mighty Blows, Size Modifiers
    """.strip())

def test_all_sample_creatures():
    # for now, just make sure all creatures can be built without encountering
    # errors
    sample_creatures = None
    with open('content/sample_creatures.yaml', 'r') as sample_creatures_file:
        sample_creatures = yaml.load(sample_creatures_file)
    for creature_name, properties in sample_creatures.items():
        if properties.get('hidden'):
            continue
        print('creature_name', creature_name)
        creature = Creature.from_sample_creature(creature_name)
        assert_equal(type(creature), Creature)

def test_all_monsters():
    monsters = None
    with open('content/monsters.yaml', 'r') as sample_creatures_file:
        monsters = yaml.load(sample_creatures_file)
    for monster_name, properties in monsters.items():
        if properties.get('hidden'):
            continue
        print('monster_name', monster_name)
        creature = Creature.from_sample_creature(monster_name)
        assert_equal(type(creature), Creature)
