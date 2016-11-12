#!/usr/bin/env python

from rise_gen.dice import Die, DieCollection
import yaml


class RiseData(object):
    data = None

    def __init__(
            self,
            **kwargs
    ):
        for key, value in kwargs.items():
            key = key.replace(' ', '_')
            setattr(self, key, value)

    @classmethod
    def init_data(cls):
        pass

    @classmethod
    def from_name(
            cls,
            thing_name
    ):
        if thing_name is None:
            return None
        if cls.data is None:
            cls.data = cls.init_data()
        relevant_data = cls.data.get(thing_name)

        for key in relevant_data:
            python_friendly_key = key.replace(' ', '_')
            relevant_data[python_friendly_key] = relevant_data.pop(key)

        if relevant_data is None:
            raise Exception(
                "Error: No data for Rise thing '{}' found".format(
                    thing_name,
                )
            )

        return cls(
            name=thing_name,
            **relevant_data
        )


class Race(RiseData):

    @property
    def space(self):
        """Return the physical space occupied by this race

        Yields:
            int: space in feet
        """

        return {
            'small': 5,
            'medium': 5,
            'large': 10,
        }[self.size]

    @property
    def reach(self):
        """Return the distance this race threatens

        Yields:
            int: reach in feet
        """

        return {
            'small': 5,
            'medium': 5,
            'large': 10,
        }[self.size]

    @classmethod
    def init_data(cls):
        with open('content/races.yaml', 'r') as races_file:
            return yaml.load(races_file)

    def __str__(self):
        return "Race({}, {}, {})".format(
            self.name,
            self.size,
            self.land_speed,
        )


class RiseClass(RiseData):

    def __init__(self, name, combat_prowess, fortitude=None, reflex=None, mental=None, class_features=None):
        super(RiseClass, self).__init__(
            name=name,
            combat_prowess=combat_prowess,
            fortitude=fortitude,
            reflex=reflex,
            mental=mental,
            class_features=class_features
        )

    @classmethod
    def init_data(cls):
        with open('content/classes.yaml', 'r') as classes_file:
            return yaml.load(classes_file)

    def __str__(self):
        return "RiseClass({}, {}, {}, {}, {})".format(
            self.name,
            self.combat_prowess,
            self.fortitude,
            self.reflex,
            self.mental,
        )

class Armor(RiseData):

    @classmethod
    def init_data(cls):
        with open('content/armor.yaml', 'r') as armor_file:
            return yaml.load(armor_file)

    def decrease_encumbrance(self):
        self.encumbrance = {
            'heavy': 'medium',
            'medium': 'light',
            'light': None,
            None: None,
        }[self.encumbrance]


class Shield(RiseData):

    @classmethod
    def init_data(cls):
        with open('content/shields.yaml', 'r') as shields_file:
            return yaml.load(shields_file)


class Weapon(RiseData):

    def __init__(self, **kwargs):
        super(Weapon, self).__init__(**kwargs)
        # convert the die to a Die object
        if hasattr(self, 'die'):
            self.dice = DieCollection(Die.from_string(self.die))
        else:
            self.dice = DieCollection()
        # set default values of None
        self.range = getattr(self, 'range', None)
        self.dual_wielding = getattr(self, 'dual_wielding', None)

    def roll_damage(self):
        return self.dice.roll()

    @classmethod
    def init_data(cls):
        with open('content/weapons.yaml', 'r') as weapons_file:
            return yaml.load(weapons_file)


def calculate_attribute_progression(progression, level):
    """Calculate an attribute's actual value based on level and progression

    The possible progressions and their purposes are as follows:
        'full': a PC's primary attribute, starting at 4 and increased at each level
        'primary': a primary attribute for a monster
        'secondary': an secondary attribute for a monster
        'tertiary': a tertiary attribute for a monster
        'bad': a penalized attribute for a monster
        <number>: the number
    """

    # key is by starting value
    return {
        None: 0,
        1: level // 4 + 1,
        2: level // 2 + 2,
        3: (level * 3) // 4 + 3,
        4: level + 3,
        5: level + 4
    }.get(progression, progression) # if not in here, just use the given value
