#!/usr/bin/env python

import argparse
from rise_gen.ability import Ability
from rise_gen.dice import Die, DieCollection, d20
from rise_gen.rise_data import (
    Armor, Race, RiseClass, Shield, Weapon, calculate_attribute_progression
)
import rise_gen.util as util

ATTRIBUTES = """
    strength
    dexterity
    constitution
    intelligence
    perception
    willpower
""".split()


class CreatureStatistics(object):
    def __init__(
            self,
            name,
            race,
            rise_class,
            attributes=None,
            level=None,
            armor=None,
            shield=None,
            weapons=None,
            feats=None,
            templates=None,
            traits=None,
            description=None,
            combat_description=None,
            size=None,
            attack_type=None,
            special_attack_name=None,
            speeds=None,
    ):
        """Create a creature with all necessary statistics, attributes, etc.

        Args:

        Yields:
            CreatureStatistics: the base statistics for a Rise creature
        """

        self.name = name
        self.race = race
        self.rise_class = rise_class
        self.attributes = attributes or dict()
        self.level = level or 1
        self.armor_name = armor
        self.shield = shield
        self.weapon_names = weapons
        self.description = description
        self.combat_description = combat_description
        self.attack_type = attack_type or 'physical'
        self.special_attack_name = special_attack_name
        self.speeds = speeds or dict()

        if isinstance(self.race, str):
            self.race = Race.from_name(self.race)
        if isinstance(self.rise_class, str):
            self.rise_class = RiseClass.from_name(self.rise_class)
        if isinstance(self.shield, str):
            self.shield = Shield.from_name(self.shield)

        self.size = size or self.race.size

        self._cache = dict()

        # add special abilities (feats, class features, etc.)
        self.abilities = list()
        try:
            for class_feature in self.rise_class.class_features:
                self.add_ability(class_feature)
        except AttributeError:
            # not all classes has class features (yet)
            pass
        if feats is not None:
            for feat in feats:
                self.add_ability(feat)
        if templates is not None:
            for template in templates:
                self.add_ability(template)
        if traits is not None:
            for trait in traits:
                self.add_ability(trait)

        self.add_ability('size modifiers')

    def add_ability(self, ability):
        """add the given ability to the creature

        Args:
            ability (string or Ability): the name of the ability
                or the ability itself
        """

        if isinstance(ability, str):
            ability = Ability.by_name(ability)
        self.abilities.append(ability)
        self.clear_cache()

    def cache(self, key, value):
        """Store a value in the cache. Also returns the value for convenience.

        Args:
            key (str): name of the key to store the value in
            value (varies): value to store in the cache.
                Usually a number.

        Yields:
            (varies): the value stored
        """

        self._cache[key] = value
        return value

    def clear_cache(self):
        """Remove all values from the creature's cache.
        This should be called when adding new abilities or modifiers.
        """
        self._cache = dict()

    def has_ability(self, ability_name, ignore_prerequisites=False):
        """Check whether the creature has a given ability.
        The creature must meet the prerequisites for the ability unless
        ignore_prerequisites is specified
        """
        relevant_abilities = [
            ability.name == ability_name
            for ability in self.abilities
        ]
        if len(relevant_abilities) >= 1:
            raise Exception("Creature has two abilities with the same name")
        elif relevant_abilities:
            relevant_ability = relevant_abilities[0]
            if ignore_prerequisites or relevant_ability.prerequisite(self):
                return True
            else:
                return False
        else:
            return False

    def roll_damage(self):
        return self.damage_dice.roll() + self.damage_bonus

    @property
    def active_abilities(self):
        return filter(
            lambda ability: ability.prerequisite(self),
            self.abilities
        )

    @property
    def attack_range(self):
        return self.weapon.range

    @property
    def reach(self):
        """The distance this race threatens in feet (int)"""
        return self.race.reach

    @property
    def space(self):
        """The physical space occupied by this race in feet (int)"""
        return self.race.space

    @property
    def weapon_encumbrance(self):
        try:
            return self.weapon.encumbrance
        except AttributeError:
            return None

    def _calculate_accuracy(self):
        """The bonus the creature has with attacks (int)"""

        if self.attack_type == 'physical':
            accuracy = 4 + max(
                self.combat_prowess,
                self.strength,
                self.dexterity if self.weapon_encumbrance == 'light' else 0
            )
            # add the automatic modifier from Perception
            if self.perception >= 0:
                accuracy += self.perception // 5
            else:
                accuracy += self.perception // 2
            for effect in self.active_effects_with_tag('accuracy'):
                accuracy = effect(self, accuracy)
            return accuracy
        elif self.attack_type == 'spell':
            # class_scaling = (self.level // 5) + 2
            class_scaling = 0
            # this feat scaling is weird and approximate, but whatever
            feat_scaling = min(4, 1 + self.level // 4)
            return self.level + class_scaling + feat_scaling
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def _calculate_attack_count(self):
        """The number of attacks this creature can make each round (int)"""

        if self.attack_type == 'physical':
            attack_count = 1 + (self.combat_prowess - 1) // 5
            for effect in self.active_effects_with_tag('attack count'):
                attack_count = effect(self, attack_count)
            return attack_count
        elif self.attack_type == 'spell':
            return 1
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def _calculate_damage_bonus(self):
        """The bonus damage this creature deals with attacks. (int)
        Does not include the base weapon damage die."""

        if self.attack_type == 'physical':
            damage_bonus = max(self.strength, self.combat_prowess) // 2

            # add the attribute bonus from strength
            if self.strength >= 0:
                damage_bonus += self.strength // 5
            else:
                damage_bonus += self.strength // 2

            # add the +1 bonus for two-handed weapons
            if self.weapon and self.weapon_encumbrance == 'heavy':
                damage_bonus += 1
            for effect in self.active_effects_with_tag('physical damage bonus'):
                damage_bonus = effect(self, damage_bonus)
            return damage_bonus
        elif self.attack_type == 'spell':
            damage_bonus = 0
            for effect in self.active_effects_with_tag('spell damage bonus'):
                damage_bonus = effect(self, damage_bonus)
            return damage_bonus
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def _calculate_damage_dice(self):
        """The dice this creature rolls for damage with its attacks (DieCollection)"""

        damage_dice = None
        if self.attack_type == 'physical':
            try:
                damage_dice = self.weapon.dice
            except AttributeError:
                damage_dice = DieCollection()
            for effect in self.active_effects_with_tag('physical damage dice'):
                damage_dice = effect(self, damage_dice)

        elif self.attack_type == 'spell':
            #TODO: make framework for named spells
            if self.special_attack_name == 'scorching ray' or self.special_attack_name == 'inflict wounds':
                damage_dice = DieCollection(
                    Die(size=6, count=self.accuracy)
                )
            else:
                raise Exception("Error: Unrecognized spell '{}'".format(self.special_attack_name))
            for effect in self.active_effects_with_tag('spell damage dice'):
                damage_dice = effect(self, damage_dice)

        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

        return damage_dice

    def _calculate_attribute(self, attribute_name):
        """Any of the creature's main attributes:
        strength, dexterity, constitution, intelligence, perception, willpower
        """
        attribute_value = calculate_attribute_progression(
            self.attributes.get(attribute_name, None),
            self.level
        )
        for effect in self.active_effects_with_tag(attribute_name):
            attribute_value = effect(self, attribute_value)

        # heavier armor halves dexterity
        if (
                attribute_name == 'dexterity'
                and self.armor
                and self.armor.encumbrance in ('medium', 'heavy')
        ):
            attribute_value = attribute_value // 2
        return attribute_value

    def _calculate_armor_check_penalty(self):
        if self.armor is None:
            penalty = 0
        else:
            penalty = self.armor.armor_check_penalty
        for effect in self.active_effects_with_tag('armor check penalty'):
            penalty = effect(self, penalty)
        return max(0, penalty)

    def _calculate_armor_defense(self):
        armor_defense = 10 + max(
            self.combat_prowess,
            self.dexterity,
            self.constitution
        )
        # add the automatic modifier from Dexterity
        if self.dexterity >= 0:
            armor_defense += self.dexterity // 5
        else:
            armor_defense += self.dexterity // 2
        if self.armor:
            armor_defense += self.armor.bonus
        if self.shield:
            armor_defense += self.shield.bonus
        for effect in self.active_effects_with_tag('armor defense'):
            armor_defense = effect(self, armor_defense)
        return armor_defense

    def _calculate_combat_prowess(self):
        prowess = self.rise_class.calculate_combat_prowess(self.level)
        for effect in self.active_effects_with_tag('combat prowess'):
            prowess = effect(self, prowess)
        return prowess

    def _calculate_critical_threshold(self):
        threshold = 20
        for effect in self.active_effects_with_tag('critical threshold'):
            threshold = effect(self, threshold)
        return threshold

    def _calculate_critical_multiplier(self):
        multiplier = 2
        for effect in self.active_effects_with_tag('critical multiplier'):
            multiplier = effect(self, multiplier)
        return multiplier

    def _calculate_fortitude(self):
        fortitude = 10 + max(
            self.constitution,
            self.strength,
            self.rise_class.calculate_base_defense(
                'fortitude',
                self.level
            )
        )
        fortitude += self.rise_class.base_class_defense_bonus('fortitude')
        # add the automatic modifier from Con
        if self.constitution >= 0:
            fortitude += self.constitution // 2
        else:
            fortitude += self.constitution
        for effect in self.active_effects_with_tag('fortitude'):
            fortitude = effect(self, fortitude)
        return fortitude

    def _calculate_hit_points(self):
        hit_points = self.level * (
            max(self.fortitude, self.mental) // 2
        )
        for effect in self.active_effects_with_tag('hit points'):
            hit_points = effect(self, hit_points)
        return hit_points

    def _calculate_maneuver_defense(self):
        maneuver_defense = 10 + max(
            self.combat_prowess,
            self.strength,
            self.dexterity
        )
        # add the automatic modifier from Dexterity
        if self.dexterity >= 0:
            maneuver_defense += self.dexterity // 5
        else:
            maneuver_defense += self.dexterity // 2
        for effect in self.active_effects_with_tag('maneuver defense'):
            maneuver_defense = effect(self, maneuver_defense)
        return maneuver_defense

    def _calculate_mental(self):
        mental = 10 + max(
            self.willpower,
            self.intelligence,
            self.rise_class.calculate_base_defense(
                'mental',
                self.level
            )
        )
        mental += self.rise_class.base_class_defense_bonus('mental')
        # add the automatic modifier from Willpower
        if self.willpower >= 0:
            mental += self.willpower // 2
        else:
            mental += self.willpower
        for effect in self.active_effects_with_tag('mental'):
            mental = effect(self, mental)
        return mental

    def _calculate_reflex(self):
        reflex = 10 + max(
            self.dexterity,
            self.perception,
            self.rise_class.calculate_base_defense(
                'reflex',
                self.level
            )
        )
        reflex += self.rise_class.base_class_defense_bonus('reflex')
        # add the automatic modifier from Dexterity
        if self.dexterity >= 0:
            reflex += self.dexterity // 5
        else:
            reflex += self.dexterity // 2
        for effect in self.active_effects_with_tag('reflex'):
            reflex = effect(self, reflex)
        return reflex

    def _calculate_land_speed(self):
        """The creature's land speed in feet (int)"""
        land_speed = self.speeds.get('land') or self.race.land_speed
        for effect in self.active_effects_with_tag('land speed') + self.active_effects_with_tag('speed'):
            land_speed = effect(self, land_speed)
        return land_speed

    def _calculate_armor(self):
        """The creature's weapon (Weapon)"""
        if self.armor_name is None:
            return None
        armor = Armor.from_name(self.armor_name)
        for effect in self.active_effects_with_tag('armor'):
            armor = effect(self, armor)
        return armor

    def _calculate_weapon(self):
        """The creature's weapon (Weapon)"""
        if self.weapon_names is None:
            return None
        weapon = Weapon.from_name(self.weapon_names[0])
        for effect in self.active_effects_with_tag('weapon'):
            weapon = effect(self, weapon)
        return weapon

    def _calculate_numerical_statistic(self, statistic_tag_name):
        """Any generic numerical statistic which is typically 0
        such as damage reduction, temporary hit points, etc.
        """
        statistic = 0
        for effect in self.active_effects_with_tag(statistic_tag_name):
            statistic = effect(self, statistic)
        return statistic

    def active_effects_with_tag(self, effect_tag):
        """Get all effects the creature has which match the given tag

        Args:
            effect_tag (string): Name of a category of effects

        Yields:
            list: Relevant effects the creature has
        """

        relevant_ability_effects = list()
        for ability in self.abilities:
            for ability_effect in ability.effects:
                if (
                        effect_tag in ability_effect.effect_tags
                        and (
                            ability.prerequisite is None
                            or ability.prerequisite(self)
                        )
                ):
                    relevant_ability_effects.append(ability_effect)
        return relevant_ability_effects

    def __str__(self):
        return '{0} {1} {2}\n{3}\n{4}\n{5}\n{6}\n{7}'.format(
            self.race.name,
            self.name,
            self.level,
            self._to_string_defenses(),
            self._to_string_attacks(),
            self._to_string_attributes(),
            self._to_string_core(),
            self._to_string_abilities(),
        )

    def _to_string_defenses(self):
        text = '; '.join([
            "[HP] {0}".format(self.hit_points) + (
                " ({0})".format(
                    self.hit_points + self.temporary_hit_points
                ) if self.temporary_hit_points else ""
            ),
            "[Defs] AD {0}, MD {1}".format(
                self.armor_defense,
                self.maneuver_defense,
            ),
            "Fort {0}, Ref {1}, Ment {2}".format(
                self.fortitude,
                self.reflex,
                self.mental,
            ),
        ])

        special_defense_text = ""
        if self.damage_reduction:
            special_defense_text += '[DR] {0}'.format(self.damage_reduction)

        if special_defense_text:
            text += "\n    " + special_defense_text

        # special defensive abilities
        return text

    def _to_string_attacks(self):
        text = ""
        attacks = [str(self.accuracy) for i in range(self.attack_count)]

        text = '; '.join([
            "[Atk] {0}: {1}".format(
                ', '.join(attacks),
                "{0}+{1}".format(
                    self.damage_dice,
                    self.damage_bonus
                )
            ),
            "[Prowess] {0}".format(
                self.combat_prowess,
            ),
        ])
        return text

    def _to_string_attributes(self):
        text = '[Attr]'
        for attribute in ATTRIBUTES:
            text += ' ' + str(getattr(self, attribute))
        return text

    def _to_string_core(self):
        return '[Space] {0}, [Reach] {1}, [Speed] {2}'.format(
            self.space,
            self.reach,
            self.land_speed,
        )

    def _to_string_abilities(self):
        text = '[Abil] ' + ', '.join(
            [name.title() for name in
             sorted([ability.name for ability in self.active_abilities])]
        )
        return text


def create_cached_property(
        property_name,
        calculation_function=None,
        calculation_args=None
):
    if calculation_function is None:
        calculation_function = '_calculate_{0}'.format(property_name)

    def get_cached_property(creature):
        try:
            return creature._cache[property_name]
        except KeyError:
            return creature.cache(
                property_name,
                getattr(creature, calculation_function)(calculation_args)
                    if calculation_args is not None
                    else getattr(creature, calculation_function)()
            )
    setattr(CreatureStatistics, property_name, property(get_cached_property))

# add cached properties to CreatureStatistics for easy access
cached_properties = """
    accuracy
    attack_count
    armor
    armor_check_penalty
    armor_defense
    combat_prowess
    critical_threshold
    critical_multiplier
    damage_bonus
    damage_dice
    fortitude
    hit_points
    land_speed
    maneuver_defense
    mental
    reflex
    weapon
""".split()
for property_name in cached_properties:
    create_cached_property(property_name)

for attribute in ATTRIBUTES:
    create_cached_property(attribute, '_calculate_attribute', attribute)
create_cached_property(
    property_name='temporary_hit_points',
    calculation_function='_calculate_numerical_statistic',
    calculation_args='temporary hit points'
)
create_cached_property(
    property_name='damage_reduction',
    calculation_function='_calculate_numerical_statistic',
    calculation_args='damage reduction'
)


class Creature(CreatureStatistics):
    """A full creature, including combat functionality"""

    sample_creatures = None

    def __init__(
            self,
            name,
            **kwargs
    ):
        super(Creature, self).__init__(name, **kwargs)

        self.refresh_combat()

    def refresh_combat(self):
        self.current_hit_points = self.hit_points
        self.zero_threshold = True
        self.refresh_round()

    def refresh_round(self):
        for effect in self.active_effects_with_tag('end of round'):
            effect(self)
        self.available_damage_reduction = self.damage_reduction
        if self.current_hit_points <= 0:
            # apply the zero threshold
            if (self.zero_threshold
                    and not self.damage_taken_this_round > self.hit_points):
                self.current_hit_points = 0
            # next round, there is no zero threshold
            self.zero_threshold = False
        else:
            self.zero_threshold = True
        self.damage_taken_this_round = 0

    def strike_hits(self, creature):
        """Make an attack against the given creature and check whether it hit

        Args:
            creature (Creature): creature being attacked

        Yields:
            bool: True if attack hit, False otherwise
        """

        roll = d20.roll()
        attack_result = roll + self.accuracy
        if roll == 20:
            attack_result += 10
        elif roll == 1:
            attack_result -= 10
        return attack_result >= creature.armor_defense

    def standard_attack(self, creature):
        """Execute a full round of strikes against the target creature

        Args:
            creature (Creature): creature being attacked

        Yields:
            dict: Results of the attack
        """

        if self.attack_type == 'physical':
            for attack_number in range(self.attack_count):
                self.strike(creature)
        elif self.attack_type == 'spell':
            self.attack_with_spell(creature)
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def strike(self, creature):
        """Execute a single strike against the given creature"""

        roll = d20.roll()
        attack_result = roll + self.accuracy
        if roll == 20:
            attack_result += 10
        elif roll == 1:
            attack_result -= 10

        if attack_result >= creature.armor_defense:
            creature.take_damage(self.roll_damage())
            # check for critical hits
            if roll >= self.critical_threshold:
                # start from 1 because the first hit was already counted
                for i in range(1, self.critical_multiplier):
                    creature.take_damage(self.roll_damage())

    def attack_with_spell(self, creature):
        """Attack the given creature with a spell"""
        roll = d20.roll()
        attack_result = roll + self.accuracy
        #TODO: implement generic framework for spells
        spell_damage = self.roll_damage()
        defense = min(creature.fortitude, creature.mental, creature.reflex)
        if attack_result >= defense:
            creature.take_damage(spell_damage)
        else:
            creature.take_damage(spell_damage // 2)

    def is_alive(self):
        return self.current_hit_points >= 0

    def heal(self, hit_points):
        """Increase current hit points by the given amount"""
        self.current_hit_points = min(self.hit_points, self.current_hit_points + hit_points)

    def take_damage(self, damage):
        """Take the given damage, applying damage reduction and other
            defensive abilities appropriately
        Hit point reduction stops at 0 unless zero_threshold is false
            or the total damage taken this round exceeds max HP

        Args:
            damage (int): Amount of damage to take

        Yields:
            int: amount of damage actually taken
        """

        if self.available_damage_reduction > 0:
            reduced_damage = max(0, damage - self.available_damage_reduction)
            self.available_damage_reduction -= (damage - reduced_damage)
            damage = reduced_damage

        self.current_hit_points -= damage
        self.damage_taken_this_round += damage

        return damage

    @classmethod
    def from_sample_creature(cls, sample_name, **kwargs):
        if cls.sample_creatures is None:
            cls.sample_creatures = util.import_yaml_file('content/sample_creatures.yaml')
            # also add monsters, which are stored separately
            cls.sample_creatures.update(util.import_yaml_file('content/monsters.yaml'))

        try:
            sample_data = cls.sample_creatures[sample_name].copy()
        except KeyError:
            raise Exception(
                "Error: Unable to recognize sample creature '{0}'".format(
                    sample_name
                )
            )

        # enforce underscores instead of spaces
        for key in sample_data:
            python_key = key.replace(' ', '_')
            if key != python_key:
                sample_data[python_key] = sample_data.pop(key)

        for key, value in kwargs.items():
            if value is not None:
                sample_data[key] = value

        return cls(
            name=sample_name,
            **sample_data
        )


def initialize_argument_parser():
    parser = argparse.ArgumentParser(
        description='Create Rise creatures',
    )
    parser.add_argument(
        '-a', '--attributes',
        dest='starting_attributes',
        nargs='*',
        help='Which attributes does this character have?'
    )
    parser.add_argument(
        '-c', '--class',
        dest='rise_class',
        type=str,
        help="name of a character's class",
    )
    parser.add_argument(
        '-l', '--level',
        dest='level',
        type=int,
        help='the level of the character',
    )
    parser.add_argument(
        '-n', '--name',
        dest='name',
        type=str,
        help="the character's name",
    )
    parser.add_argument(
        '-r', '--race',
        default='human',
        dest='race',
        type=str,
        help="the character's race",
    )
    parser.add_argument(
        '-s', '--sample',
        dest='sample_creature',
        nargs='*',
        type=str,
        help="Create a sample character instead of a new character",
    )
    parser.add_argument(
        '-w', '--weapon',
        dest='weapon',
        type=str,
        help="the character's weapon",
    )
    return vars(parser.parse_args())


def main():
    args = initialize_argument_parser()

    if args['sample_creature']:
        for sample_name in args['sample_creature']:
            sample_creature = Creature.from_sample_creature(
                sample_name,
                level=args.get('level'),
                starting_attributes=args.get('starting_attributes'),
            )
            print(sample_creature)
    else:
        if args['rise_class']:
            rise_class = RiseClass.from_name(args['rise_class'])
        else:
            raise Exception("Error: No class provided")

        race = Race.from_name(args['race'])

        if 'weapon' in args:
            weapon = Weapon.from_name(args['weapon'])
        else:
            weapon = None

        if args['attributes']:
            starting_attributes = args['attributes']
        else:
            raise Exception("Error: no attributes provided")

        creature = Creature(
            name=args.get('name') or args['rise_class'],
            race=race,
            rise_class=rise_class,
            starting_attributes=starting_attributes,
            level=args['level'],
            weapon=weapon,
        )
        print(creature)

if __name__ == "__main__":
    main()
