#!/usr/bin/env python3

from rise_gen.dice import DicePool
import yaml

SKILLS = """
    climb
    jump
    sprint
    swim
    balance
    escape artist
    ride
    sleight of hand
    stealth
    tumble
    craft
    devices
    disguise
    heal
    knowledge
    linguistics
    awareness
    creature handling
    sense motive
    spellcraft
    survival
    intimidate
    perform
    profession
    bluff
    persuasion
""".split()

ATTRIBUTES = """
    strength
    dexterity
    constitution
    intelligence
    perception
    willpower
""".split()


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
        if relevant_data is None:
            raise Exception("Error finding data for '{}'".format(thing_name))

        # pull the keys into a list to keep them from changing as we change the
        # dictionary
        for key in list(relevant_data.keys()):
            python_friendly_key = key.replace(' ', '_')
            if python_friendly_key != key:
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

    def __init__(self, name, size, land_speed):
        super(Race, self).__init__(
            name=name,
            size=size,
            land_speed=land_speed,
        )

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


class MonsterType(RiseData):

    def __init__(self, name, fortitude, reflex, mental, abilities=None):
        super(MonsterType, self).__init__(
            name=name,
            fortitude=fortitude,
            reflex=reflex,
            mental=mental,
            abilities=abilities
        )

    @classmethod
    def init_data(cls):
        with open('content/monster_types.yaml', 'r') as types_file:
            return yaml.load(types_file)

    def __str__(self):
        return "MonsterType({}, {}, {}, {})".format(
            self.name,
            self.fortitude,
            self.reflex,
            self.mental,
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
        self.dice = DicePool.from_string(self.die)
        # set default values of None
        self.range = getattr(self, 'range', None)
        self.dual_wielding = getattr(self, 'dual_wielding', None)

    def roll_damage(self):
        return self.dice.roll()

    @classmethod
    def init_data(cls):
        with open('content/weapons.yaml', 'r') as weapons_file:
            return yaml.load(weapons_file)


class Skill(RiseData):

    def __init__(self, name, attribute, sense=False, encumbrance_penalty=False):
        super().__init__(name=name, attribute=attribute, sense=sense, encumbrance_penalty=encumbrance_penalty)

    @classmethod
    def init_data(cls):
        with open('content/skills.yaml', 'r') as skills_file:
            return yaml.load(skills_file)

    def __str__(self):
        return "Skill({}, {}, {}, {})".format(
            self.name,
            self.attribute,
            self.sense,
            self.encumbrance,
        )


def calculate_attribute_progression(progression, level):
    """Calculate an attribute's actual value based on level and progression"""

    # key is by starting value
    return {
        None: 0,
        -2: -2,
        -1: -1,
        0: 0,
        1: level,
        2: level + 1,
        3: level + 2,
        4: level + 3,
    }[progression]


def calculate_skill_ranks(skill_points, level):
    """Calculate an skill's ranks based on level and skill points"""

    # key is by starting value
    return {
        None: 0,
        0: 0,
        1: level // 2 + 1,
        2: level + 2,
    }[skill_points]


def calculate_skill_modifier(skill_points, level, attribute):
    """Calculate total skill modifier based on level, attribute, and skill points"""

    return max(
        calculate_skill_ranks(skill_points, level),
        {
            None: attribute // 2,
            0: attribute // 2,
            1: max(attribute, level // 2 + 1),
            2: 3 + max(attribute, level),
        }[skill_points] if attribute is not None else 0
    )
