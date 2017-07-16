from nose.tools import assert_equal, nottest
from rise_gen.creature import Creature
from rise_gen.dice import DicePool
import yaml

def setup():
    pass

def teardown():
    pass

def test_fighter_properties():
    c = Creature.from_sample_creature('fighter', level=1)
    correct_properties = {
        'accuracy': 2,
        'encumbrance_penalty': 3,
        'armor_defense': 10,
        'damage_bonus': 1,
        'damage_dice': DicePool(10),
        'fortitude': 12,
        'hit_points': 16,
        'mental': 8,
        'land_speed': 30,
        'name': 'fighter',
        'reach': 5,
        'reflex': 9,
        'space': 5,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equal(getattr(c, key), correct_properties[key], f'{key} property is wrong')

def test_fighter_properties_at_higher_level():
    c = Creature.from_sample_creature('fighter', level=10)
    correct_properties = {
        'accuracy': 11,
        'encumbrance_penalty': 3,
        'armor_defense': 19,
        'damage_bonus': 2,
        'damage_dice': DicePool(8, 4),
        'fortitude': 21,
        'hit_points': 81,
        'mental': 17,
        'name': 'fighter',
        'reach': 5,
        'reflex': 18,
        'space': 5,
        'land_speed': 30,
        'weapon_encumbrance': 'medium',
    }
    for key in sorted(correct_properties.keys()):
        assert_equal(getattr(c, key), correct_properties[key], f'{key} property is wrong')

def test_fighter_string():
    c = Creature.from_sample_creature('fighter', level=1)
    assert_equal(str(c), """
human fighter Fighter 1
[HP] 16; [Defs] AD 10; Fort 12, Ref 9, Ment 8
[Atk] 2: 1d10+1; [Prowess] 1
[Attr] 3 0 3 0 0 0
[Space] 5, [Reach] 5, [Speed] 30
[Abil] Automatic Damage Scaling, Challenge Rating, Constitution, Dexterity, Intelligence, Magic Items, Martial Excellence, Perception, Size Modifiers, Strength, Willpower
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

# TODO: enable this once monsters are fixed
@nottest
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
