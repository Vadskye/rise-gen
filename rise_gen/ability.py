#!/usr/bin/env python

from rise_gen.dice import Die, quick_roll
from rise_gen.rise_data import ATTRIBUTES, SKILLS
import re

POSSIBLE_EFFECT_TAGS = [
    'accuracy',
    'armor',
    'armor check penalty',
    'armor defense',
    'attack count',
    'physical damage bonus',
    'spell damage bonus',
    'weapon damage dice',
    'physical damage dice',
    'spell damage dice',
    'combat prowess',
    'critical multiplier',
    'critical threshold',
    'damage reduction',
    'end of round',
    'first hit',
    'fortitude',
    'hit points',
    'maneuver accuracy',
    'maneuver defense',
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

class Ability:

    ability_definitions = None

    def __init__(
        self,
        name,
        effects = None,
        prerequisite=None,
        effect_strength=None,
        tags=None,
    ):
        self.name = name
        self.effects = effects
        self.prerequisite = prerequisite or (lambda creature: True)
        self.effect_strength = effect_strength
        self.tags = tags

        if self.effect_strength is not None and self.effects is not None:
            for effect in self.effects:
                effect.effect_strength = self.effect_strength

    def has_tag(self, tag):
        return self.tags is not None and tag in self.tags

    @classmethod
    def by_name(cls, ability_name, effect_strength=None):
        if Ability.ability_definitions is None:
            Ability.ability_definitions = get_ability_definitions()
        try:
            ability_definition = Ability.ability_definitions[ability_name]
            return Ability(
                name=ability_name,
                effect_strength=effect_strength,
                **ability_definition
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

    def __str__(self):
        if self.effect_strength is None:
            return self.name
        elif isinstance(self.effect_strength, int) or re.match(r'\d+$', self.effect_strength):
            # raw numbers should be treated as modifiers
            return "{} {}{}".format(self.name, "+" if self.effect_strength >= 0 else "-", self.effect_strength)
        else:
            return "{} {}".format(self.name, self.effect_strength)


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

class VariableModifier(AbilityEffect):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.effect_strength = 0

    def __call__(self, creature, value):
        return self.effect(creature, value, self.effect_strength)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.effect_tags)


class ModifierInPlace(AbilityEffect):
    def __call__(self, creature, value):
        self.effect(creature, value)
        return value

def plus(modifier):
    return lambda creature, value: value + modifier

def min_level(level, class_name=None):
    if class_name is None:
        return lambda creature: creature.level >= level
    else:
        return lambda creature: creature.levels.get(class_name, 0) >= level


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
        'barbarian damage reduction': {
            'effects': [
                Modifier(['damage reduction'],
                         lambda creature, value: creature.level + value),
            ],
            'prerequisite': lambda creature: creature.base_class.name == 'barbarian',
        },
        'fast movement': {
            'effects': [
                Modifier(['speed'], plus(10)),
            ],
            'prerequisite': min_level(2, 'barbarian')
        },
        'durable': {
            'effects': [
                Modifier(['fortitude'],
                         lambda creature, value: value + 4),
            ],
            'prerequisite': min_level(9, 'barbarian'),
        },
        'larger than life': {
            'effects': [
                ModifierInPlace(['weapon'],
                                lambda creature, weapon: [weapon.dice.increase_size()
                                                          for i in range(2)]),
            ],
            'prerequisite': min_level(8, 'barbarian')
        },
        'larger than belief': {
            'effects': [
                ModifierInPlace(['weapon'],
                                lambda creature, weapon: [weapon.dice.increase_size()
                                                          for i in range(2)]),
            ],
            'prerequisite': min_level(16, 'barbarian')
        },
        'rage': {
            'effects': [
                Modifier(['temporary hit points'],
                         lambda creature, value: max(value, creature.willpower * 2)),
                Modifier(['physical damage bonus', 'fortitude', 'mental'],
                         lambda creature, value: value + (creature.levels['barbarian'] // 5) + 2),
                # undo the effect of the fortitude/mental bonus on HP
                Modifier(['hit points'],
                         lambda creature, value: value - (((creature.levels['barbarian'] // 5) + 2) // 2) * creature.willpower),
                Modifier(['armor defense', 'maneuver defense'],
                         lambda creature, value: value - 2),
            ],
            'prerequisite': min_level(1, 'barbarian')
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
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + (creature.levels['ranger'] // 5) + 2),
                Modifier(['armor defense', 'maneuver defense', 'fortitude', 'reflex', 'mental'],
                         lambda creature, value: value + (creature.levels['ranger'] // 5) + 2),
                # undo the hp bonus from the quarry
                Modifier(['hit points'],
                         lambda creature, value: value - (((creature.levels['ranger'] // 5) + 2) // 2) * creature.level),
            ],
            'prerequisite': min_level(1, 'ranger')
        },

        # ROGUE
        'sneak attack': {
            'effects': [
                # correct behavior: the first hit deals d6 = level/2
                # and subsequent attacks have no bonus
                Modifier(['first hit'],
                           lambda creature, value: value + quick_roll(6, creature.levels['rogue'] + 1) // 2),
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
                True # creature.preception >= 3
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
        'mighty blows': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + 1 + (creature.level + 1) // 4),
            ],
            'prerequisite': lambda creature: (
                creature.level >= 5
                and creature.strength >= 6
                and creature.attack_range is None
            )
        },
        'heavy weapon fighting': {
            'effects': [
                ModifierInPlace(['weapon damage dice'],
                         lambda creature, damage_dice: damage_dice.resize_dice(min(4,1 + (creature.level + 1) // 4))),
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

    # MISC
    misc = {
        'magic items': {
            'effects': [
                Modifier(['physical damage bonus'],
                         lambda creature, value: value + creature.level // 3),
                Modifier(['temporary hit points'],
                         lambda creature, value: max(
                             value,
                             (creature.level // 3) * creature.level
                         )),
                # ModifierInPlace(['spell damage dice'],
                #          lambda creature, dice: setattr(dice.dice[0], 'count', dice.dice[0].count + creature.level // 3))
                # Modifier(['spell damage bonus'],
                #         lambda creature, value: value + ((creature.level + 2) // 2) * (creature.level // 3)),
                # Modifier(['spellpower'],
                #         lambda creature, value: value + (creature.level // 3)),
            ],
            'tags': set(['hidden']),
        },
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
                Modifier(['maneuver defense', 'maneuver accuracy', 'fortitude'],
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
                ModifierInPlace(['weapon damage dice'],
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
                VariableModifier(['armor defense'],
                               lambda creature, value, effect_strength: value + effect_strength),
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
        'critical multiplier': {
            'effects': [
                Modifier(['critical multiplier'],
                         lambda creature, value: value + 1),
            ],
        },
        'critical threshold': {
            'effects': [
                Modifier(['critical threshold'],
                         lambda creature, value: value - 1),
            ],
        },
    }

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
            sense['tags'].add(['sense'])
        else:
            sense['tags'] = set(['sense'])

    # TEMPLATES
    templates = {
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
                         lambda creature, value: creature.level * 50),
                Modifier(['armor defense'],
                         lambda creature, value: creature.level + 16),
                Modifier(['fortitude', 'mental', 'maneuver defense'],
                         lambda creature, value: creature.level + 14),
                Modifier(['reflex'],
                         lambda creature, value: creature.level + 12),
                Modifier(['accuracy'],
                         lambda creature, value: -50),
                Modifier(['attack count'],
                         lambda creature, value: 1),
            ],
        },
    }

    # TRAITS
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
        'behemoth size': {
            'effects': [
                Modifier(['size'],
                         # find the current size in the list and go to the next
                         # larger one
                         # this fails for colossal; for now, that is a feature
                         lambda creature, value: SIZES[SIZES.index(value) + creature.level // 4]),
            ],
            'prerequisite': min_level(4, 'behemoth')
        },
        'brute force': {
            'effects': [
                Modifier(['physical damage bonus'],
                                lambda creature, value: value + creature.levels['slayer'] // 2),
            ],
            'prerequisite': min_level(1, 'slayer')
        },
        'draining touch': {
            # this should only be applied to creatures with a single touch attack
            'effects': [
                ModifierInPlace(['weapon damage dice'],
                                lambda creature, damage_dice: damage_dice.resize_dice(2)),
                Modifier(['physical damage bonus'],
                          lambda creature, value: creature.power // 2),
            ],
        },
        'durable': {
            'effects': [
                Modifier(['hit points'],
                         lambda creature, value: value + creature.power * 2),
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
                Modifier(['fortitude'],
                              lambda creature, value: value + 4),
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
                Modifier(['armor defense'],
                               lambda creature, value: value + 2),
            ],
        },
        'increased size': {
            'effects': [
                Modifier(['size'],
                         # find the current size in the list and go to the next
                         # larger one
                         # this fails for colossal; for now, that is a feature
                         lambda creature, value: SIZES[SIZES.index(value) + creature.level // 6]),
            ],
            'prerequisite': lambda creature: creature.level >= 6,
        },
        'mighty will': {
            'effects': [
                Modifier(['mental'],
                         lambda creature, value: value + 4)
            ],
        },
        'resist damage': {
            'effects': [
                Modifier(['damage reduction'],
                         lambda creature, value: creature.power + value),
            ],
        },
        'tough hide': {
            'effects': [
                Modifier(['armor defense'],
                         lambda creature, value: value + 2),
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
