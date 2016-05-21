from nose.tools import *
from rise_gen.ability_leveler import AbilityLeveler
import rise_gen.util as util

def setup():
    pass

def teardown():
    pass

def test_ability_simple():
    ability = AbilityLeveler('simple', {
        'damage': 'normal',
        'range': 'close',
    })
    assert_equal(ability.level(), 4)

def test_spell_levels():
    true_spell_levels = util.import_yaml_file('content/spell_levels.yaml')
    spells = util.import_yaml_file('content/spells.yaml')
    for spell_name in spells:
        print(spell_name)
        spell = AbilityLeveler(spell_name, spells[spell_name])
        assert_equal(spell.level('spell'), true_spell_levels[spell_name])
