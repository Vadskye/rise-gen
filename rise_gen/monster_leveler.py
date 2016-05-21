#!/usr/bin/env python

from docopt import docopt
from rise_gen.leveler import Leveler
import rise_gen.util as util

doc = """
Usage:
    monster_leveler [options]

Options:
    -h, --help      Show this screen and exit
    -v, --verbose   Show more output
"""

RAW_MODIFIERS = util.import_yaml_file('content/monster_modifiers.yaml')

class MonsterLeveler(Leveler):

    def _attributes_modifier(self):
        """We don't care about the names - just the values"""
        modifier = 0
        for name in self.attributes:
            value = self.attributes[name]
            if isinstance(value, str):
                modifier += RAW_MODIFIERS['attributes'][value]
            elif isinstance(value, int):
                pass
            else:
                self.die("Unable to recognize attribute value '{}'".format(value))
        return modifier

    def _speeds_modifier(self):
        modifier = 0
        for speed_type in self.speeds:
            modifier += getattr(
                self,
                '_{}_speed_modifier'.format(speed_type)
            )()
        return modifier

    def _land_speed_modifier(self):
        difference_type = None
        land_speed = self.speeds['land']
        if land_speed == 0:
            difference_type = 'none'
        else:
            speed_difference = land_speed / default_land_speed(self.size)
            if speed_difference < 1:
                difference_type = 'slower'
            elif speed_difference == 1:
                difference_type = 'normal'
            elif speed_difference < 2:
                difference_type = 'faster'
            else:
                difference_type = 'double'
        return RAW_MODIFIERS['land speed'][difference_type]

    def _swim_speed_modifier(self):
        return RAW_MODIFIERS['swim speed']

    def _size_modifier(self):
        return RAW_MODIFIERS['size'][self.size]

    def _weapons_modifier(self):
        return len(self.weapons) * RAW_MODIFIERS['weapons']

    def effective_level(self):
        return self.level()
MonsterLeveler.import_config('content/monster_leveler_config.yaml')


def calculate_monster_levels(data):
    levels = dict()
    for name in data:
        monster = MonsterLeveler(name, data[name])
        levels[name] = monster.effective_level()
    return levels


def default_land_speed(size):
    return {
        'fine': 5,
        'diminuitive': 10,
        'tiny': 15,
        'small': 20,
        'medium': 30,
        'large': 40,
        'huge': 50,
        'gargantuan': 60,
        'colossal': 70,
    }[size]

def main(args):
    data = util.import_yaml_file('content/monsters.yaml')
    monster_levels = calculate_monster_levels(data)
    for monster_name in sorted(monster_levels.keys()):
        print("{}: {}".format(
            monster_name,
            monster_levels[monster_name]
        ))

if __name__ == "__main__":
    main(docopt(doc))
