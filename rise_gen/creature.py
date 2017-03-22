#!/usr/bin/env python3

import argparse
import copy
from rise_gen.ability import Ability
from rise_gen.dice import Die, DieCollection, d10
from rise_gen.rise_data import (
    ATTRIBUTES, SKILLS,
    Armor, MonsterType, Race, RiseClass, Shield, Skill, Weapon,
    calculate_attribute_progression, calculate_skill_modifier
)
import random
import rise_gen.latex as latex
import rise_gen.util as util

DEFENSE_BASE=5

class CreatureStatistics(object):
    def __init__(
            self,
            name,
            levels,
            armor=None,
            attack_type='physical',
            attributes=None,
            base_class=None,
            encounter=None,
            feats=None,
            languages=None,
            level=None,
            monster_type=None,
            race=None,
            skill_points=None,
            shield=None,
            size='medium',
            special_attack_name=None,
            speeds=None,
            subtraits=None,
            templates=None,
            traits=None,
            weapons=None,
    ):
        """Create a creature with all necessary statistics, attributes, etc.

        Args:

        Yields:
            CreatureStatistics: the base statistics for a Rise creature
        """

        self.name = name
        # levels in each class
        self.levels = levels
        # equipment is given as strings, but we we want them to be objects
        self.armor_name = armor
        self.shield_name = shield
        self.weapon_names = weapons

        # it's useful to track the "original" size
        # separately from the size property
        self.base_size = size

        # these are just stored directly
        self.attack_type = attack_type
        self.base_class = base_class
        self.encounter = encounter
        self.feats = feats
        self.languages = languages
        self.level = level
        self.skill_points = skill_points
        self.special_attack_name = special_attack_name
        self.speeds = speeds
        self.starting_attributes = attributes
        self.subtraits = subtraits
        self.templates = templates
        self.traits = traits

        self.challenge_rating = len(self.templates) if self.templates else 1

        # these are usually given as strings
        # but we want to store them as objects
        if isinstance(monster_type, str):
            self.monster_type = MonsterType.from_name(monster_type)
        else:
            self.monster_type = monster_type
        if isinstance(race, str):
            self.race = Race.from_name(race)
        else:
            self.race = race
        if isinstance(shield, str):
            self.shield = Shield.from_name(shield)
        else:
            self.shield = shield

        if self.level is None:
            # determine total level from the 'levels' given
            self.level = sum(self.levels.values())
        else:
            # if we're given an explicit level, adjust the levels in self.levels
            # to sum to the given level
            total_levels = sum(self.levels.values())
            if self.level < total_levels:
                raise Exception("Level {} is too low for this multiclass character ({})".format(self.level, self.levels))
            # maintain the ratio between the levels
            for class_name, level in self.levels.items():
                self.levels[class_name] = level * self.level // total_levels
            if sum(self.levels.values()) != self.level:
                raise Exception("Level {} is not possible to express exactly for this multiclass character".format(self.level))

        # Skills are given as a dictionary of skill name -> skill points
        # We also want to store a dictionary of skill name -> Skill object
        if self.skill_points is not None:
            self.skills = dict()
            for skill_name in self.skill_points.keys():
                self.skills[skill_name] = Skill.from_name(skill_name)
        else:
            self.skills = None

        # construct classes from the 'levels' given
        self.classes = dict()
        for class_name in self.levels:
            rise_class = RiseClass.from_name(class_name)
            if rise_class is None:
                raise Exception("Unable to recognize class '{}'".format(class_name))
            # monsters inherit fortitude, reflex, mental from their type
            if rise_class.fortitude is None and rise_class.mental is None and rise_class.reflex is None:
                rise_class.fortitude = self.monster_type.fortitude
                rise_class.mental = self.monster_type.mental
                rise_class.reflex = self.monster_type.reflex
            self.classes[class_name] = rise_class

        # use the same object that we already created above
        # rather than creating a separate RiseClass object
        if isinstance(self.base_class, str):
            self.base_class = self.classes[self.base_class]

        # assume the base class if only one class is given
        if self.base_class is None:
            if len(self.classes) == 1:
                self.base_class = next(iter(self.classes.values()))
            else:
                raise Exception("Error: No base class given")

        # use the race's size as a default if no size is specified
        if self.base_size is None and self.race is not None:
            self.base_size = self.race.size

        self._cache = dict()

        # add special abilities (feats, class features, etc.)
        self.abilities = list()
        if self.monster_type and self.monster_type.abilities:
            for ability in self.monster_type.abilities:
                self.add_ability(ability)
        for rise_class in self.classes.values():
            if rise_class.class_features:
                for class_feature in rise_class.class_features:
                    self.add_ability(class_feature)
        if self.feats is not None:
            for feat in self.feats:
                self.add_ability(feat)
        if self.subtraits is not None:
            for subtrait in self.subtraits:
                self.add_ability(subtrait)
        if self.templates is not None:
            # hackery to allow duplicate templates for CR purposes
            # without duplicating abilities
            for template in set(self.templates):
                self.add_ability(template)
        if self.traits is not None:
            for trait in self.traits:
                self.add_ability(trait)

        self.add_ability('size modifiers')
        self.add_ability('challenge rating')

    def add_ability(self, ability):
        """add the given ability to the creature

        Args:
            ability (string or Ability): the name of the ability
                or the ability itself
        """

        if isinstance(ability, str):
            ability = Ability.by_name(ability)
        elif isinstance(ability, dict):
            # some abilities also include values for the ability
            if len(ability.keys()) != 1:
                raise Exception("Invalid dictionary ability '{}'".format(ability))
            ability_name = next(iter(ability))
            ability = Ability.by_name(ability_name, ability[ability_name])
        elif not isinstance(ability, Ability):
            raise Exception("Unable to recognize type of ability '{}'".format(ability))
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
    def visible_abilities(self):
        return filter(
            lambda ability: ability.prerequisite(self) and not ability.has_tag('hidden'),
            self.abilities
        )

    @property
    def action_count(self):
        if self.challenge_rating == 2:
            if random.random() >= 0.5:
                return 2
            else:
                return 1
        else:
            return max(1, self.challenge_rating - 1)

    @property
    def attack_range(self):
        return self.weapon.range

    @property
    def reach(self):
        """The distance this creature threatens in feet (int)"""
        return {
            'small': 5,
            'medium': 5,
            'large': 10,
            'huge': 20,
            'gargantuan': 30,
            'colossal': 40,
        }[self.size]

    @property
    def space(self):
        """The physical space occupied by this creature in feet (int)"""

        return {
            'small': 5,
            'medium': 5,
            'large': 10,
            'huge': 20,
            'gargantuan': 30,
            'colossal': 40,
        }[self.size]

    @property
    def weapon_encumbrance(self):
        try:
            return self.weapon.encumbrance
        except AttributeError:
            return None

    def base_progression(self, progression_type):
        if self.rise_class is not None:
            return getattr(self.rise_class, progression_type)
        else:
            raise Exception("Unable to determine progression: creature is invalid")

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
            class_scaling = 2
            # this feat scaling is weird and approximate, but whatever
            # feat_scaling = min(4, (self.level - 1) // 4)
            feat_scaling = 0 # if self.level < 10 else 2
            return self.level + class_scaling + feat_scaling
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def _calculate_damage_bonus(self):
        """The bonus damage this creature deals with attacks. (int)
        Does not include the base weapon damage die."""

        if self.attack_type == 'physical':
            damage_bonus = max(self.strength, self.combat_prowess)

            # add the attribute bonus from strength
            if self.strength >= 0:
                damage_bonus += self.strength // 5
            else:
                damage_bonus += self.strength // 2

            # add the +1 bonus for two-handed weapons
            if self.weapon and self.weapon_encumbrance == 'heavy' and not self.attack_range:
                damage_bonus += 2
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
            # separate effects on the weapon, such as size modifiers
            # from effects on the creature, such as sneak attacks
            for effect in self.active_effects_with_tag('weapon damage dice'):
                self.weapon.dice = effect(self, self.weapon.dice)
            damage_dice = copy.deepcopy(self.weapon.dice)
            for effect in self.active_effects_with_tag('physical damage dice'):
                damage_dice = effect(self, damage_dice)

        elif self.attack_type == 'spell':
            # TODO: make framework for named spells
            # we use cantrips instead of full spells until 4th level
            if self.level <= 3:
                damage_dice = DieCollection(
                    Die(size=6, count=self.spellpower // 2)
                )
            elif self.level <= 10:
                damage_dice = DieCollection(
                    Die(size=6, count=self.spellpower)
                )
            else:
                damage_dice = DieCollection(
                    Die(size=8, count=self.spellpower)
                )
            if not (self.special_attack_name == 'scorching ray' or self.special_attack_name == 'inflict wounds'):
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
            self.starting_attributes.get(attribute_name, None) if self.starting_attributes else None,
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

    def _calculate_encumbrance_penalty(self):
        if self.armor is None:
            penalty = 0
        else:
            penalty = self.armor.encumbrance_penalty
        for effect in self.active_effects_with_tag('encumbrance penalty'):
            penalty = effect(self, penalty)
        return max(0, penalty)

    def _calculate_armor_defense(self):
        armor_defense = DEFENSE_BASE + max(
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
        prowess = base_class_combat_prowess_bonus(self.base_class.combat_prowess)
        for class_name, rise_class in self.classes.items():
            prowess += calculate_combat_prowess(
                rise_class.combat_prowess, self.levels[class_name])
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
        fortitude = DEFENSE_BASE + max(
            self.constitution,
            self.strength,
            sum([calculate_base_defense(rise_class.fortitude, self.levels[class_name])
                 for class_name, rise_class in self.classes.items()])

        )
        fortitude += base_class_defense_bonus(self.base_class.fortitude)
        # add the automatic modifier from Con
        if self.constitution >= 0:
            fortitude += self.constitution // 2
        else:
            fortitude += self.constitution
        for effect in self.active_effects_with_tag('fortitude'):
            fortitude = effect(self, fortitude)
        return fortitude

    def _calculate_hit_points(self):
        best_defense = max(self.fortitude, self.mental)
        hit_points = best_defense + self.level * 4
        for effect in self.active_effects_with_tag('hit points'):
            hit_points = effect(self, hit_points)
        return hit_points

    def _calculate_maneuver_defense(self):
        maneuver_defense = DEFENSE_BASE + max(
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
        mental = DEFENSE_BASE + max(
            self.willpower,
            self.intelligence,
            sum([calculate_base_defense(rise_class.mental, self.levels[class_name])
                 for class_name, rise_class in self.classes.items()])
        )
        mental += base_class_defense_bonus(self.base_class.mental)
        # add the automatic modifier from Willpower
        if self.willpower >= 0:
            mental += self.willpower // 2
        else:
            mental += self.willpower
        for effect in self.active_effects_with_tag('mental'):
            mental = effect(self, mental)
        return mental

    def _calculate_reflex(self):
        reflex = DEFENSE_BASE + max(
            self.dexterity,
            self.perception,
            sum([calculate_base_defense(rise_class.reflex, self.levels[class_name])
                 for class_name, rise_class in self.classes.items()])
        )
        reflex += base_class_defense_bonus(self.base_class.reflex)
        # add the modifier for shields
        if self.shield is not None:
            reflex += self.shield.bonus
        # add the automatic modifier from Dexterity
        if self.dexterity >= 0:
            reflex += self.dexterity // 5
        else:
            reflex += self.dexterity // 2
        for effect in self.active_effects_with_tag('reflex'):
            reflex = effect(self, reflex)
        return reflex

    def _calculate_spellpower(self):
        spellpower = self.level + 2
        for effect in self.active_effects_with_tag('spellpower'):
            spellpower = effect(self, spellpower)
        return spellpower

    def _calculate_land_speed(self):
        """The creature's land speed in feet (int)"""
        if self.speeds is None or self.speeds.get('land') is None:
            land_speed = default_land_speed(self.size)
        else:
            land_speed = self.speeds.get('land')
        for effect in self.active_effects_with_tag('land speed') + self.active_effects_with_tag('speed'):
            land_speed = effect(self, land_speed)
        return land_speed

    def _calculate_armor(self):
        """The creature's armor (Armor)"""
        if self.armor_name is None:
            return None
        armor = Armor.from_name(self.armor_name)
        for effect in self.active_effects_with_tag('armor'):
            armor = effect(self, armor)
        return armor

    def _calculate_weapon(self):
        """The creature's weapon (Weapon)"""
        if self.weapon_names is None:
            return Weapon.from_name('no weapon')
        weapon = Weapon.from_name(self.weapon_names[0])
        for effect in self.active_effects_with_tag('weapon'):
            weapon = effect(self, weapon)
        return weapon

    def _calculate_power(self):
        """A monster's power (int)"""
        power = self.level + self.challenge_rating
        for effect in self.active_effects_with_tag('power'):
            power = effect(self, power)
        return power

    def _calculate_size(self):
        """A creature's size (str)"""
        size = self.base_size or 'medium'
        for effect in self.active_effects_with_tag('size'):
            size = effect(self, size)
        return size

    def _calculate_skill(self, skill_name):
        """Any of the creature's skills"""
        # for now, ignore all skills not specified on character creation
        # this is wrong, but simpler
        if self.skills is None or self.skills.get(skill_name) is None:
            return 0

        attribute_name = self.skills[skill_name].attribute
        if attribute_name is not None:
            attribute = getattr(self, attribute_name)
        else:
            attribute = None
        skill_modifier = calculate_skill_modifier(
            self.skill_points[skill_name],
            self.level,
            attribute
        )
        if self.skills[skill_name].encumbrance_penalty:
            skill_modifier -= self.encumbrance_penalty
        for effect in self.active_effects_with_tag(skill_name):
            skill_modifier = effect(self, skill_modifier)
        return skill_modifier

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
            if ability.effects:
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
            self.race.name if self.race else self.monster_type.name,
            self.name,
            self._to_string_levels(),
            self._to_string_defenses(),
            self._to_string_attacks(),
            self._to_string_attributes(),
            self._to_string_core(),
            self._to_string_abilities(),
        )

    def _to_string_levels(self):
        text = ", ".join(sorted([
            "{} {}".format(name.capitalize() if name == self.base_class.name else name, level)
            for name, level in self.levels.items()
        ]))
        if self.challenge_rating != 1:
            text += f" [CR {self.challenge_rating}]"
        return text

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
        attack = str(self.accuracy)

        text = '; '.join([
            "[Atk] {0}: {1}".format(
                attack,
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
    armor
    encumbrance_penalty
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
    power
    size
    spellpower
    weapon
""".split()
for property_name in cached_properties:
    create_cached_property(property_name)

for attribute in ATTRIBUTES:
    create_cached_property(attribute, '_calculate_attribute', attribute)
for skill in SKILLS:
    create_cached_property(skill, '_calculate_skill', skill)
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
        super().__init__(name, **kwargs)

        self.refresh_combat()

    def refresh_combat(self):
        self.current_hit_points = self.hit_points + self.temporary_hit_points
        self.alive = True
        self.zero_threshold = True
        self.refresh_round()

    def refresh_round(self):
        for effect in self.active_effects_with_tag('end of round'):
            effect(self)
        self.alive = self.current_hit_points >= 0
        self.available_damage_reduction = self.damage_reduction
        self.hit_once = False
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

        roll = d10.roll()
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
            self.strike(creature)
        elif self.attack_type == 'spell':
            self.attack_with_spell(creature)
        else:
            raise Exception("Error: invalid attack type '{0}'".format(self.attack_type))

    def check_hit(self, creature):
        """Test if a single strike hits against the given creature"""

        roll = d10.roll()
        attack_result = roll + self.accuracy
        if roll == 20:
            attack_result += 10
        elif roll == 1:
            attack_result -= 10
        if self.attack_type == 'physical':
            defense = creature.armor_defense
        else:
            defense = min(creature.fortitude, creature.mental, creature.reflex)

        return attack_result >= defense

    def strike(self, creature):
        """Execute a single strike against the given creature"""

        roll = d10.roll()
        attack_result = roll + self.accuracy
        if roll == 20:
            attack_result += 10
        elif roll == 1:
            attack_result -= 10

        if attack_result >= creature.armor_defense:
            if (self.weapon.dual_wielding):
                # damage = max(self.roll_damage(), self.roll_damage())
                damage = self.roll_damage() + self.weapon.roll_damage()
            else:
                damage = self.roll_damage()
            if not self.hit_once:
                for effect in self.active_effects_with_tag('first hit'):
                    damage = effect(self, damage)
            # creature.take_damage(self.roll_damage())
            # check for critical hits
            if roll >= self.critical_threshold:
                # start from 1 because the first hit was already counted
                for i in range(1, self.critical_multiplier):
                    damage += self.roll_damage()
                    if not self.hit_once:
                        for effect in self.active_effects_with_tag('first hit'):
                            damage = effect(self, damage)
            creature.take_damage(damage)
            self.hit_once = True

    def attack_with_spell(self, creature):
        """Attack the given creature with a spell"""
        roll = d10.roll()
        attack_result = roll + self.spellpower
        #TODO: implement generic framework for spells
        spell_damage = self.roll_damage()
        defense = min(creature.fortitude, creature.mental, creature.reflex)
        # critical success double damage
        if attack_result >= defense + 10:
            creature.take_damage(spell_damage * 2)
        elif attack_result >= defense:
            creature.take_damage(spell_damage)
        else:
            creature.take_damage(spell_damage // 2)

    def is_alive(self):
        return self.alive

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
            sample_properties = copy.deepcopy(cls.sample_creatures[sample_name])
        except KeyError:
            raise Exception(
                "Error: Unable to recognize sample creature '{0}'".format(
                    sample_name
                )
            )

        # enforce underscores instead of spaces
        for key in sample_properties:
            python_key = key.replace(' ', '_')
            if key != python_key:
                sample_properties[python_key] = sample_properties.pop(key)

        for key, value in kwargs.items():
            if value is not None:
                sample_properties[key] = value

        return cls(
            name=sample_name,
            levels=sample_properties.pop('levels'),
            **sample_properties,
        )

def base_class_combat_prowess_bonus(progression):
    return {
        'good': 2,
        'average': 2,
        'poor': 1,
    }[progression]

def base_class_defense_bonus(progression):
    return {
        'good': 4,
        'average': 2,
        'poor': 0,
    }[progression]

def calculate_combat_prowess(progression, level):
    return {
        'good': level,
        'average': (level * 4) // 5,
        'poor': (level * 2) // 3,
    }[progression]

def calculate_base_defense(progression, level):
    return level

def default_land_speed(size):
    return {
        'fine': 10,
        'diminuitive': 15,
        'tiny': 20,
        'small': 25,
        'medium': 30,
        'large': 40,
        'huge': 50,
        'gargantuan': 60,
        'colossal': 70,
    }[size]

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
    parser.add_argument(
        '-x', '--latex',
        dest='latex',
        action='store_true',
        help="print the LaTeX for the creature",
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
            if (args['latex']):
                print(latex.monster_latex(sample_creature))
            else:
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

        if args['starting_attributes']:
            starting_attributes = args['starting_attributes']
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
