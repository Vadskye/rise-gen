from nose.tools import *
from rise_gen.monster_leveler import MonsterLeveler
import rise_gen.util as util

def setup():
    pass

def teardown():
    pass

def test_simple_monster():
    monster = MonsterLeveler('simple', {
        'weapons': ['bite', 'claw'],
    })
    assert_equal(monster.level(), 0.5)

def test_monster_levels():
    true_monster_levels = util.import_yaml_file('content/monster_levels.yaml')
    monsters = util.import_yaml_file('content/monsters.yaml')
    for monster_name in sorted(monsters.keys()):
        print(monster_name)
        monster = MonsterLeveler(monster_name, monsters[monster_name])
        assert_equal(monster.level(), true_monster_levels[monster_name])
