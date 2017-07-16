#!/usr/bin/env python3

import argparse
import copy
from rise_gen.creature_statistics import CreatureStatistics
from rise_gen.dice import d10
from rise_gen.rise_data import (
    Race, RiseClass, Weapon,
)
import rise_gen.latex as latex
import rise_gen.util as util

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
        self.critical_hits = 0

    def refresh_round(self):
        for effect in self.active_effects_with_tag('end of round'):
            effect(self)
        self.alive = self.current_hit_points >= 0
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

    # It can be useful to return both dual strike rolls,
    # but most of the time we just want the better of the two, as if it was a
    # normal attack roll.
    def attack_roll(self, return_both_dual_strikes=False):
        roll = d10.roll(explode=True)
        alternate_roll = None
        if (self.weapon.dual_wielding):
            alternate_roll = d10.roll(explode=True)
            if return_both_dual_strikes:
                return max(roll, alternate_roll) + self.accuracy, min(roll, alternate_roll) + self.accuracy
            else:
                return max(roll, alternate_roll) + self.accuracy
        return roll + self.accuracy

    def check_hit(self, creature, attack_type=None):
        """Test if a single strike hits against the given creature"""

        if (attack_type or self.attack_type) == 'physical':
            defense = creature.armor_defense
        else:
            defense = min(creature.fortitude, creature.mental, creature.reflex)

        return self.attack_roll() >= defense

    def strike(self, creature):
        """Execute a single strike against the given creature"""

        damage = None
        if self.weapon.dual_wielding:
            better, worse = self.attack_roll(return_both_dual_strikes=True)
            if better >= creature.armor_defense:
                bonus = None
                # This is too strong - should be for the feat
                # bonus = 1 if better >= creature.armor_defense else None
                damage = self.roll_damage(bonus)
                # Critical success deals damage with the other weapon,
                # but we don't differentiate the weapons yet
                if better >= creature.armor_defense + 10:
                    damage += self.roll_damage(bonus)
        else:
            attack_roll = self.attack_roll()
            if attack_roll >= creature.armor_defense:
                damage = self.roll_damage()
                # critical success deals double damage
                if attack_roll >= creature.armor_defense + 10:
                    damage += self.roll_damage()
                    # temp debug
                    self.critical_hits += 1
        if damage is not None:
            for effect in self.active_effects_with_tag('first hit'):
                damage = effect(self, damage)
            creature.take_damage(damage)

    def attack_with_spell(self, creature):
        """Attack the given creature with a spell"""
        # TODO: implement generic framework for spells
        defense = min(creature.fortitude, creature.mental, creature.reflex)
        attack_roll = self.attack_roll()
        # critical success deal double damage
        if attack_roll >= defense:
            damage = self.roll_damage()
            if attack_roll >= defense + 10:
                damage += self.roll_damage()
                # temp debug
                self.critical_hits += 1
            creature.take_damage(damage)
        else:
            pass
            # creature.take_damage(self.roll_damage() // 2)

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
