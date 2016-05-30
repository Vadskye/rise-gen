#!/usr/bin/env python

from rise_gen.dice import Die

POSSIBLE_EFFECT_TAGS = [
    'accuracy',
    'armor',
    'armor check penalty',
    'armor defense',
    'attack count',
    'physical damage bonus',
    'spell damage bonus',
    'physical damage dice',
    'spell damage dice',
    'combat prowess',
    'constitution',
    'critical multiplier',
    'critical threshold',
    'damage reduction',
    'dexterity',
    'end of round',
    'fortitude',
    'hit points',
    'intelligence',
    'maneuver accuracy',
    'maneuver defense',
    'mental',
    'perception',
    'reflex',
    'temporary hit points',
    'speed',
    'strength',
    'weapon',
    'willpower',
]


class Ability:

    ability_definitions = None

    def __init__(
        self,
        name,
        effects,
        prerequisite=None,
    ):
        self.name = name
        self.effects = effects
        self.prerequisite = prerequisite or (lambda creature: True)

    @classmethod
    def by_name(cls, ability_name):
        if Ability.ability_definitions is None:
            Ability.ability_definitions = get_ability_definitions()
        try:
            ability_definition = Ability.ability_definitions[ability_name]
            return Ability(
                name=ability_name,
                effects=ability_definition.get('effects'),
                prerequisite=ability_definition.get('prerequisite')
            )
        except KeyError:
            raise Exception(
                "Error: unable to recognize ability '{}'".format(ability_name)
            )

    def __repr__(self):
        return "{}({}, {}, {})".format(
            self.__class__.__name__,
            self.name,
            self.effects,
            "pre" if self.prerequisite is not None else None,
        )


class AbilityEffect:
    def __init__(
        self,
        effect_tags,
        effect,
    ):
        for tag in effect_tags:
            if tag not in POSSIBLE_EFFECT_TAGS:
                raise Exception(
                    "Error: Unable to recognize effect tag '{}'".format(tag)
                )
        self.effect_tags = effect_tags
        self.effect = effect

    def __call__(self, creature):
        return self.effect(creature)


class Modifier(AbilityEffect):
    def __call__(self, creature, value):
        return self.effect(creature, value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.effect_tags)


class ModifierInPlace(AbilityEffect):
    def __call__(self, creature, value):
        self.effect(creature, value)
        return value


def get_ability_definitions():
    """This defines the set of all possible abilities. The Ability class uses
    this to create abilities on the fly as needed.
    The dictionary is constructed from multiple separate kinds of abilities:
    class features, feats, and monster traits

    Yields:
    {
        <ability name>: {
            'effects': [
                AbilityEffect(<effect args>),
                ...
            ],
            'prerequisite': lambda creature: <true if prerequisites met>
        },
        ...
    }
    """

    class_features = {

        # BARBARIAN
        'damage reduction': {
            'effects': [
                Modifier(['damage reduction'],
                         lambda creature, value: creature.level + value),
            ],
            'prerequisite': lambda creature: creature.level >= 1
        },
        'fast movement': {
            'effects': [
                Modifier(['speed'],
                         lambda creature, value: value + 10),
            ],
            'prerequisite': lambda creature: creature.level >= 2
        },
        'larger than life': {
            'effects': [
                ModifierInPlace(['weapon'],
                                lambda creature, weapon: [weapon.dice.increase_size()
                                                          for i in range(2)]),
            ],
            'prerequisite': lambda creature: creature.level >= 7
        },
        'larger than belief': {
            'effects': [
                ModifierInPlace(['weapon'],
                                lambda creature, weapon: [weapon.dice.increase_size()
                                                          for i in range(2)]),
            ],
            'prerequisite': lambda creature: creature.level >= 16
        },
        'rage': {
            'effects': [
                Modifier(['temporary hit points'],
                         lambda creature, value: max(value, creature.willpower * 2)),
                Modifier(['physical damage bonus', 'fortitude', 'mental'],
                         lambda creature, value: value + (creature.level // 5) + 2),
                # undo the effect of the fortitude/mental bonus on HP
                Modifier(['hit points'],
                         lambda creature, value: value - (((creature.level // 5) + 2) // 2) * creature.level),
                Modifier(['armor defense', 'maneuver defense'],
                         lambda creature, value: value - 2),
            ],
            'prerequisite': lambda creature: creature.level >= 1
        },

        # FIGHTER
        'greater weapon discipline': {
            'effects': [
                Modifier(['critical threshold'],
                         lambda creature, value: value - 1),
            ],
            'prerequisite': lambda creature: creature.level >= 15
        },
        'improved weapon discipline': {
            'effects': [
                Modifier(['critical multiplier'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: creature.level >= 9
        },
        'weapon discipline': {
            'effects': [
                Modifier(['accuracy'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: creature.level >= 3
        },

        # RANGER
        'quarry': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + (creature.level // 5) + 2),
                Modifier(['armor defense', 'maneuver defense', 'fortitude', 'reflex', 'mental'],
                         lambda creature, value: value + (creature.level // 5) + 2),
                # undo the hp bonus from the quarry
                Modifier(['hit points'],
                         lambda creature, value: value - (((creature.level // 5) + 2) // 2) * creature.level),
            ],
        },

        # ROGUE
        'sneak attack': {
            'effects': [
                ModifierInPlace(['physical damage dice'],
                                lambda creature, damage_dice: damage_dice.add_die(
                                    # we don't have a concept of "the first hit"
                                    # so it should be a mix of level/2 and level/4
                                    # for now use level/2 since it might be too low anyway
                                    Die(size=6, count=(creature.level + 1) // 2)
                                )),
            ],
        },
    }

    feats = {
        'deadly aim': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 2),
            ],
            'prerequisite': lambda creature: (
                creature.perception >= 5
                and creature.attack_range is not None
            )
        },
        'dodge': {
            'effects': [],
        },
        'heartseeker': {
            'effects': [
                Modifier(['critical threshold'],
                         lambda creature, value: value - 1),
            ],
            'prerequisite': lambda creature: creature.combat_prowess >= 8
        },
        'mighty blows': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: (
                creature.strength >= 5
                and creature.attack_range is None
            )
        },
        'power attack': {
            'effects': [
                Modifier(['accuracy'],
                         lambda creature, value: value - 2),
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 2),
            ],
            'prerequisite': lambda creature: (
                creature.strength >= 3
                and creature.attack_range is None
            )
        },
        'weapon finesse': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: (
                creature.dexterity >= 3
                and creature.attack_range is None
                and creature.weapon.encumbrance == 'light'
            )
        },
    }

    misc = {
        'size modifiers': {
            'effects': [
                Modifier(['accuracy', 'armor defense', 'reflex'],
                         lambda creature, value: (
                             value + {
                                 'fine': 8,
                                 'diminuitive': 4,
                                 'tiny': 2,
                                 'small': 1,
                                 'medium': 0,
                                 'large': -1,
                                 'huge': -2,
                                 'gargantuan': -4,
                                 'colossal': -8,
                             }[creature.size]
                         )),
                Modifier(['maneuver defense', 'maneuver accuracy'],
                         lambda creature, value: (
                             value + {
                                 'fine': -16,
                                 'diminuitive': -12,
                                 'tiny': -8,
                                 'small': -4,
                                 'medium': 0,
                                 'large': 4,
                                 'huge': 8,
                                 'gargantuan': 12,
                                 'colossal': 16,
                             }[creature.size]
                         )),
                ModifierInPlace(['physical damage dice'],
                                lambda creature, damage_dice: damage_dice.resize_dice(
                                    {
                                        'fine': -4,
                                        'diminuitive': -3,
                                        'tiny': -2,
                                        'small': -1,
                                        'medium': 0,
                                        'large': 2,
                                        'huge': 4,
                                        'gargantuan': 6,
                                        'colossal': 8,
                                    }[creature.size]
                                )),
            ],
        },
        'extra attack': {
            'effects': [
                Modifier(['attack count'],
                         lambda creature, value: value + 1),
            ],
        },
        'accuracy': {
            'effects': [
                Modifier(['accuracy'],
                         lambda creature, value: value + 1),
            ],
        },
        'damage bonus': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1),
            ],
        },
        'critical multiplier': {
            'effects': [
                Modifier(['critical multiplier'],
                         lambda creature, value: value + 1),
            ],
        },
    }

    templates = {
        'martial': {
            'effects': [
                Modifier(['combat prowess'],
                         lambda creature, value: creature.level + 2),
            ],
        },
        'summoned monster': {
            'effects': [
                Modifier(['combat prowess'],
                         lambda creature, value: creature.level),
                Modifier(['armor defense', 'fortitude',
                          'reflex', 'mental', 'maneuver defense'],
                         lambda creature, value: creature.level + 10),
            ],
        },
        'training dummy': {
            'effects': [
                Modifier(['hit points'],
                         lambda creature, value: 1000),
                Modifier(['armor defense'],
                         lambda creature, value: creature.level + 16),
                Modifier(['fortitude', 'mental', 'maneuver defense'],
                         lambda creature, value: creature.level + 14),
                Modifier(['reflex'],
                         lambda creature, value: creature.level + 10),
            ],
        },
    }

    traits = {
        'arcanite mech': {
            'effects': [
                Modifier(['fortitude', 'mental'],
                         lambda creature, value: value + 4),
                Modifier(['strength', 'constitution'],
                         lambda creature, value: value + 2),
                Modifier(['damage reduction'],
                         lambda creature, value: value + creature.level),
                # should drain HP
                # for now, only trolls wear it, so ignore that
            ],
        },
        'arcanite sigil - armor': {
            'effects': [
                Modifier(['armor defense'],
                         lambda creature, value: value + 3),
            ],
        },
        'arcanite sigil - flaming fists': {
            'effects': [
                ModifierInPlace(['physical damage dice'],
                                lambda creature, damage_dice: damage_dice.add_die(
                                    Die(size=6, count=creature.level // 2)
                                )),
            ],
        },
        'arcanite sigil - mind control': {
            'effects': [
                Modifier(['mental'],
                         lambda creature, value: value + 5),
            ],
        },
        'armor discipline (agility)': {
            'effects': [
                Modifier(['armor check penalty'],
                         lambda creature, value: max(0, value - 2)),
                Modifier(['armor defense'],
                         # technically, this should be implemented by decreasing the
                         # armor encumbrance
                         # but that also should go with increasing the category of
                         # armor used, since you would upgrade armor categories
                         # this can be approximated by simply increasing armor
                         # defense
                         lambda creature, value: value + (
                             4 if creature.level >= 13 else
                             (2 if creature.level >= 7 else value)
                         )),
            ],
        },
        'armor discipline (resilience)': {
            'effects': [
                Modifier(['armor defense'],
                         lambda creature, value: value + 1),
                Modifier(['damage reduction'],
                         lambda creature, value: value + (
                             creature.level if creature.level >= 7 else 0
                         )),
            ],
        },
        'fast healing': {
            'effects': [
                AbilityEffect(
                    ['end of round'],
                    lambda creature: creature.heal(creature.level)
                ),
            ],
        },
        'improved grab': {
            'effects': [],
        },
        'magic items': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + creature.level // 3),
                Modifier(['temporary hit points'],
                         lambda creature, value: max(
                             value,
                             (creature.level // 3) * creature.level
                         )),
            ],
        },
        'tough hide': {
            'effects': [
                Modifier(['armor defense'],
                         lambda creature, value: value + 2),
            ],
        },

        # these traits have no effects that can be calculated for now
        'enslave': {'effects': []},
        'mucus cloud': {'effects': []},
        'slime': {'effects': []},
    }

    all_abilities = dict()
    all_abilities.update(class_features)
    all_abilities.update(feats)
    all_abilities.update(misc)
    all_abilities.update(templates)
    all_abilities.update(traits)
    return all_abilities
