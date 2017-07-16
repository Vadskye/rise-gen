#!/usr/bin/env python3

from rise_gen.rise_data import ATTRIBUTES, SKILLS
from rise_gen.abilities.ability_effect import AbilityEffect
from rise_gen.abilities.modifiers import Modifier, ModifierInPlace, VariableModifier

POSSIBLE_EFFECT_TAGS = [
    'accuracy',
    'armor',
    'armor check penalty',
    'armor defense',
    'attack count',
    'critical damage',
    'extra rounds',
    'physical damage bonus',
    'spell damage bonus',
    'weapon damage dice',
    'physical damage dice',
    'critical multiplier',
    'critical threshold',
    'damage reduction',
    'end of round',
    'fortitude',
    'hit points',
    'magical damage dice',
    'mental',
    'power',
    'reflex',
    'spellpower',
    'temporary hit points',
    'size',
    'speed',
    'weapon',
] + ATTRIBUTES + SKILLS

SIZES = ['fine', 'diminuitive', 'tiny', 'small', 'medium', 'large', 'huge', 'gargantuan', 'colossal']


def attribute_scale(attribute, per_five=True):
    if per_five:
        return attribute // 5 if attribute >= 0 else attribute // 2
    else:
        return attribute // 2 if attribute >= 0 else attribute


def plus(modifier):
    return lambda creature, value: value + modifier


def strike_damage_modifier(die_increments):
    return ModifierInPlace(['physical damage dice'],
                           lambda creature, damage_dice: damage_dice.increase_size(die_increments))


def min_level(level, class_name=None, template=None):
    if class_name is not None:
        return lambda creature: creature.levels.get(class_name, 0) >= level
    elif template is not None:
        return lambda creature: creature.level >= level and template in creature.templates
    else:
        return lambda creature: creature.level >= level


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
        'fast movement': {
            'effects': [
                Modifier(['speed'], plus(10)),
            ],
            'prerequisite': min_level(2, 'barbarian')
        },
        'durable': {
            'effects': [
                Modifier(['fortitude'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': min_level(4, 'barbarian'),
        },
        'larger than life': {
            'effects': [strike_damage_modifier(1)],
            'prerequisite': min_level(5, 'barbarian'),
        },
        'larger than belief': {
            'effects': [strike_damage_modifier(1)],
            'prerequisite': min_level(11, 'barbarian'),
        },
        'primal resilience': {
            'effects': [
                Modifier(['fortitude', 'mental'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': min_level(8, 'barbarian'),
        },
        'rage': {
            'effects': [
                Modifier(['damage reduction'],
                         lambda creature, value: value + creature.level),
                strike_damage_modifier(1),
            ],
            'prerequisite': min_level(1, 'barbarian'),
        },
        'titan of battle': {
            'effects': [strike_damage_modifier(1)],
            'prerequisite': min_level(17, 'barbarian'),
        },

        # FIGHTER
        'martial excellence': {
            'effects': [
                Modifier(['accuracy', 'armor defense', 'reflex', 'physical damage bonus'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: creature.base_class.name == 'fighter'
        },
        'greater weapon discipline': {
            'effects': [
                Modifier(['critical threshold'],
                         lambda creature, value: value - 1),
            ],
            'prerequisite': min_level(14, 'fighter')
        },
        'improved weapon discipline': {
            'effects': [
                Modifier(['critical multiplier'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': min_level(8, 'fighter')
        },
        'weapon discipline': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': min_level(4, 'fighter')
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
                             5 if creature.levels['fighter'] >= 20 else (
                                 4 if creature.levels['fighter'] >= 12 else 2
                             )
                         )),
                Modifier(['reflex'],
                         lambda creature, value: value + (
                             5 if creature.levels['fighter'] >= 19 else (
                                 4 if creature.levels['fighter'] >= 17 else 0
                             )
                         )),
            ],
            'prerequisite': min_level(6, 'fighter')
        },
        'armor discipline (resilience)': {
            'effects': [
                Modifier(['damage reduction'],
                         lambda creature, value: value + creature.levels['fighter'] * (
                             2 if creature.levels['fighter'] >= 20 else 1
                         )),
                Modifier(['armor defense'],
                         lambda creature, value: value + (1 if creature.levels['fighter'] >= 12 else 0)),
                Modifier(['fortitude'],
                         lambda creature, value: value + (
                             4 if creature.levels['fighter'] >= 18 else 0
                         )),
            ],
            'prerequisite': min_level(6, 'fighter')
        },

        # RANGER
        'quarry': {
            'effects': [
                Modifier(
                    ['physical damage bonus'],
                    lambda creature, value: value + (creature.levels['ranger'] // 5) + 2
                ),
                Modifier(
                    ['armor defense', 'fortitude', 'reflex', 'mental'],
                    lambda creature, value: value + (creature.levels['ranger'] // 5) + 2
                ),
                # undo the hp bonus from the quarry
                Modifier(
                    ['hit points'],
                    lambda creature, value: value - (((creature.levels['ranger'] // 5) + 2) // 2) * creature.level
                ),
            ],
            'prerequisite': min_level(1, 'ranger')
        },

        # ROGUE
        'sneak attack': {
            'effects': [
                ModifierInPlace(
                    ['physical damage dice'],
                    lambda creature, damage_dice: damage_dice.increase_size((creature.levels['rogue'] + 1) // 2),
                ),
            ],
            'prerequisite': min_level(1, 'rogue')
        },

        # MONSTER TYPE
        'limited intelligence': {
            'effects': [],
            'tags': set(['hidden']),
        },
    }

    # FEATS
    feats = {
        'deadly aim': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + (creature.level + 1) // 4),
            ],
            'prerequisite': lambda creature: (
                creature.level >= 5
                and creature.perception >= 6
                and creature.attack_range is not None
            )
        },
        'devastating magic': {
            'effects': [
                Modifier(['spell damage bonus'],
                         lambda creature, value: value + creature.spellpower * (2 if creature.level >= 19 else 1)),
            ],
            'prerequisite': lambda creature: creature.level >= 13,
        },
        # this is an incredibly rough approximation
        'counterattack': {
            'effects': [
                Modifier(['attack count'],
                         lambda creature, value: value + (
                             2 if creature.level >= 15 else 1
                         )),
            ],
            'prerequisite': lambda creature: (
                creature.level >= 5
                and creature.dexterity >= 6
            )
        },
        'defensive fighting': {
            'effects': [
                Modifier(['armor defense', 'reflex'],
                         lambda creature, value: value + (3 if creature.level >= 3 else 2)),
                Modifier(['physical damage bonus'],
                         lambda creature, value: value - (0 if creature.level >= 11 else (
                             1 if creature.level >= 7 else 2
                         ))),
            ],
        },
        'precise attack': {
            'effects': [
                Modifier(['accuracy'],
                         lambda creature, value: value + (3 if creature.level >= 3 else 2)),
                Modifier(['physical damage bonus'],
                         lambda creature, value: value - (0 if creature.level >= 11 else (
                             1 if creature.level >= 7 else 2
                         ))),
            ],
            'prerequisite': lambda creature: (
                True  # creature.preception >= 3
            ),
        },
        'legendary speed': {
            'effects': [
                Modifier(['attack count'],
                         lambda creature, value: value + 1),
            ],
            'prerequisite': lambda creature: (
                creature.level >= 13
                # and creature.dexterity >= 12
            ),
        },
        'weapon style, heavy': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1 + (creature.level + 1) // 4),
            ],
            'prerequisite': lambda creature: (
                creature.strength >= 3
                and creature.attack_range is None
                and creature.weapon.encumbrance == 'heavy'
            )
        },
        'heavy weapon fighting': {
            'effects': [
                ModifierInPlace(
                    ['weapon damage dice'],
                    lambda creature, damage_dice: damage_dice.resize(
                        min(4, 1 + (creature.level + 1) // 4)
                    )
                ),
            ],
            'prerequisite': lambda creature: (
                creature.strength >= 3
                and creature.attack_range is None
                and creature.weapon.encumbrance == 'heavy'
            )
        },
        'two weapon fighting': {
            'effects': [
                Modifier(['accuracy'],
                         lambda creature, value: value + (2 if creature.level >= 3 else 1)),
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + (2 if creature.level >= 11 else
                                                          (1 if creature.level >= 7 else 0))),
            ],
            'prerequisite': lambda creature: (
                creature.dexterity >= 3
                and creature.weapon.dual_wielding
            )
        },
        'shielded fighting': {
            'effects': [
                Modifier(['armor defense', 'reflex'],
                         lambda creature, value: value + (2 if creature.level >= 7 else 1)),
            ],
            'prerequisite': lambda creature: (
                creature.shield is not None
            )
        },
        'weapon finesse': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1 + (creature.level + 1) // 4),
            ],
            'prerequisite': lambda creature: (
                creature.dexterity >= 3
                and creature.attack_range is None
                and creature.weapon.encumbrance == 'light'
            )
        },
    }

    def challenge_rating_hp_multiplier(cr):
        if cr <= 1:
            return 0
        elif cr == 2:
            return 0.5
        else:
            return cr - 2

    # MISC
    misc = {
        'strength': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'dexterity': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'constitution': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'intelligence': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'perception': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'willpower': {
            'effects': [],
            'tags': set(['hidden']),
        },
        'challenge rating': {
            'effects': [
                Modifier(
                    ['hit points'],
                    lambda creature, value: value + int(
                        challenge_rating_hp_multiplier(creature.challenge_rating) * value
                    )
                ),
            ],
            'tags': set(['hidden']),
        },
        'magic items': {
            'effects': [
            ],
            'tags': set(['hidden']),
        },
        'automatic damage scaling': {
            'effects': [
                ModifierInPlace(
                    ['weapon damage dice'],
                    lambda creature, damage_dice: damage_dice.resize(
                        max(creature.level, creature.strength) // 2
                    ),
                ),
                ModifierInPlace(
                    ['magical damage dice'],
                    lambda creature, damage_dice: damage_dice.resize(
                        max(creature.spellpower, creature.willpower) // 2  # auto scaling from spellpower
                        + creature.level // 6  # +1d for +3 spell levels
                    ),
                ),
            ],
            'tags': set(['hidden']),
        },
        'size modifiers': {
            'effects': [
                Modifier(['reflex'],
                         lambda creature, value: (
                             value + {
                                 'fine': 8,
                                 'diminuitive': 6,
                                 'tiny': 4,
                                 'small': 2,
                                 'medium': 0,
                                 'large': -2,
                                 'huge': -4,
                                 'gargantuan': -6,
                                 'colossal': -8,
                             }[creature.size]
                         )),
                Modifier(['fortitude'],
                         lambda creature, value: (
                             value + {
                                 'fine': -8,
                                 'diminuitive': -6,
                                 'tiny': -4,
                                 'small': -2,
                                 'medium': 0,
                                 'large': 2,
                                 'huge': 4,
                                 'gargantuan': 6,
                                 'colossal': 8,
                             }[creature.size]
                         )),
                ModifierInPlace(['weapon damage dice'],
                                lambda creature, damage_dice: damage_dice.resize(
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
            'tags': set(['hidden']),
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
        'natural armor': {
            'effects': [
                VariableModifier(
                    ['armor defense'],
                    lambda creature, value, effect_strength: value + effect_strength
                ),
            ],
        },
        'extraplanar body': {
            'tags': set(['hidden']),
        },
        'mindless': {
            'tags': set(['hidden']),
        },
        'necromantic body': {
            'tags': set(['hidden']),
        },
        'nonliving': {
            'tags': set(['hidden']),
        },
        'nonsentient': {
            'tags': set(['hidden']),
        },
        'telepathy': {},

        # testing abilities
        'critical threshold': {
            'effects': [
                Modifier(['critical threshold'],
                         lambda creature, value: value - 1),
            ],
        },
        'damage reduction': {
            'effects': [
                Modifier(
                    ['damage reduction'],
                    lambda creature, value: value + creature.level,
                ),
            ],
        },
        'buff/damage': {
            'effects': [
                strike_damage_modifier(2)
            ],
        },
        'buff/accuracy': {
            'effects': [
                Modifier(
                    ['accuracy'],
                    lambda creature, value: value + 2,
                ),
            ],
        },
        'buff/defenses': {
            'effects': [
                Modifier(
                    ['armor defense', 'fortitude', 'reflex', 'mental'],
                    lambda creature, value: value + 2,
                ),
            ],
        },
        'extra round': {
            'effects': [
                Modifier(
                    ['extra rounds'],
                    lambda creature, value: value + 1,
                ),
            ],
        },
        'overwhelmed': {
            'effects': [
                Modifier(
                    ['armor defense', 'reflex'],
                    lambda creature, value: value - 2,
                ),
            ],
        },
    }
    for ability in misc.values():
        if 'tags' in ability:
            ability['tags'].add('misc')
        else:
            ability['tags'] = set(['misc'])

    # SENSES
    # pretty much all senses have no effects
    # but this makes it easy to add senses with effects later
    senses = dict()
    sense_names = ['darkvision', 'lifesense', 'lifesight', 'low-light vision',
                   'blindsense', 'blindsight',
                   'scent', 'tremorsense', 'tremorsight', 'truesight']
    for name in sense_names:
        senses[name] = dict()
    for sense in senses.values():
        if 'tags' in sense:
            sense['tags'].add('sense')
        else:
            sense['tags'] = set(['sense'])

    # TEMPLATES
    templates = {
        'adept': {
            'effects': [
                Modifier(['power'],
                         lambda creature, value: value + 2),
            ],
        },
        'behemoth': {
            'effects': [
                Modifier(['hit points'],
                         lambda creature, value: value + creature.power * 2),
            ],
        },
        'slayer': {
            'effects': [strike_damage_modifier(2)],
        },
        'summoned monster': {
            'effects': [
                Modifier(['armor defense', 'fortitude',
                          'reflex', 'mental'],
                         lambda creature, value: creature.level + 10),
            ],
        },
        'training dummy': {
            'effects': [
                Modifier(['hit points'],
                         lambda creature, value: 500),
                Modifier(['armor defense'],
                         lambda creature, value: creature.level + 5),
                Modifier(['fortitude', 'mental'],
                         lambda creature, value: creature.level + 5),
                Modifier(['reflex'],
                         lambda creature, value: creature.level + 5),
                Modifier(['accuracy'],
                         lambda creature, value: -50),
            ],
        },
    }
    for template in templates.values():
        if 'tags' in template:
            template['tags'].add('template')
        else:
            template['tags'] = set(['template'])

    # TRAITS
    traits = {
        'brute force': {
            'effects': [
                Modifier(
                    ['physical damage bonus'],
                    lambda creature, value: value + creature.level // 2
                ),
            ],
            'prerequisite': lambda creature: 'slayer' in creature.templates,
        },
        'defensive, armor': {
            'effects': [
                Modifier(['armor defense'],
                         lambda creature, value: value + 2 + max(0, (creature.level - 2) // 4)),
            ],
        },
        'draining touch': {
            # this should only be applied to creatures with a single touch attack
            'effects': [
                ModifierInPlace(['weapon damage dice'],
                                lambda creature, damage_dice: damage_dice.resize(2)),
                Modifier(
                    ['physical damage bonus'],
                    lambda creature, value: creature.power // 2
                ),
            ],
        },
        'evasive': {
            'effects': [
                Modifier(['armor defense', 'reflex'],
                         lambda creature, value: value + 2),
            ],
            'prerequisite': lambda creature: creature.dexterity >= 5,
        },
        'great fortitude': {
            'effects': [
                Modifier(
                    ['fortitude'],
                    lambda creature, value: value + 4
                ),
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
        'improved natural armor': {
            'effects': [
                Modifier(
                    ['armor defense'],
                    lambda creature, value: value + 2
                ),
            ],
        },
        'increased size': {
            'effects': [
                Modifier(['size'],
                         # find the current size in the list and go to the next
                         # larger one
                         # this fails for colossal; for now, that is a feature
                         lambda creature, value: SIZES[
                             SIZES.index(value)
                             + (creature.level + 4) // 8
                             + max(0, (creature.level - 4) // 8 if 'behemoth' in creature.templates else 0)
                         ]),
            ],
            'prerequisite': lambda creature: creature.level >= 4,
        },
        'resist damage': {
            'effects': [
                Modifier(
                    ['damage reduction'],
                    lambda creature, value: value + (creature.power if creature.level < 10 else creature.power * 2)
                ),
            ],
        },

        # these traits have no effects that can be calculated for now
        'attribute mastery': {},
        'boulder toss': {},
        'breath weapon: cone': {},
        'breath weapon: line': {},
        'burrower': {},
        'damaging aura': {},
        'damaging ray': {},
        'flight': {},
        'humanoid form': {},
        'incorporeal': {},
        'innate magic': {},
        'magical ability': {},
        'magical retribution': {},
        'magical strike': {},
        'multistrike': {},
        'myriad magical abilities': {},
        'natural energy': {},
        'natural grab': {},
        'natural venom': {},
        'petrifying gaze': {},
        'resist magic': {},
        'rend': {},
        'skilled': {},
        'spellcaster': {},
        'spit web': {},
        'superior senses': {},
    }
    for trait in traits.values():
        if 'tags' in trait:
            trait['tags'].add(['monster_trait'])
        else:
            trait['tags'] = set(['monster_trait'])

    all_abilities = dict()
    all_abilities.update(class_features)
    all_abilities.update(feats)
    all_abilities.update(misc)
    all_abilities.update(senses)
    all_abilities.update(templates)
    all_abilities.update(traits)
    return all_abilities
