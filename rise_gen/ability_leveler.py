#!/usr/bin/env python

from docopt import docopt
from rise_gen.leveler import Leveler
import rise_gen.util as util

doc = """
Usage:
    ability_leveler class [options]
    ability_leveler feats [options]
    ability_leveler items [options]
    ability_leveler rituals [options]
    ability_leveler spells [options]
    ability_leveler (-h | --help)

Options:
    -a, --ability <ability>  Only show information for the given ability
    -h, --help               Show this screen and exit
    -v, --verbose            Show more output
"""

RAW_MODIFIERS = util.import_yaml_file('content/ability_modifiers.yaml')

def is_close(x, y, threshold=1):
    """Test whether x is within <threshold> of y

    Args:
        x (int)
        y (int)
        threshold (int)

    Yields:
        bool
    """
    return abs(x - y) <= threshold


class AbilityLeveler(Leveler):
    primary_properties = list()

    def _init_derived_properties(self):
        """Generate top-level properties that can be deduced from other properties"""
        # generate area_size, area_shape, and area_type
        if self.area is None:
            self.area_size = None
            self.area_shape = None
            self.area_type = None
        else:
            try:
                self.area_size, self.area_shape, self.area_type = \
                    self.area.split()
            except KeyError:
                self.die("has invalid area '{0}'".format(
                    self.area
                ))

        # generate duration_type
        if self.duration is None:
            self.duration_type = None
        else:
            if self.buffs is not None:
                if self.range == 'personal':
                    self.duration_type = 'personal buff'
                elif self.noncombat:
                    self.duration_type = 'noncombat buff'
                elif self.trigger:
                    self.duration_type = 'trigger'
                else:
                    self.duration_type = 'nonpersonal buff'
            elif self.knowledge is not None:
                self.duration_type = 'personal buff'
            elif self.battlefield_effects is not None:
                self.duration_type = 'battlefield effect'
            elif self.conditions is not None:
                self.duration_type = 'condition'
            elif self.damage is not None:
                self.duration_type = 'damage over time'
            elif self.has_nested():
                self.duration_type = 'subeffect'
            else:
                self.die("could not determine duration_type")

        # generate limit_affected_type
        if self.limit_affected is None:
            self.limit_affected_type = None
        else:
            if self.buffs is not None:
                self.limit_affected_type = 'buff'
            else:
                self.limit_affected_type = 'normal'

        # generate targets_type
        if self.area is not None:
            self.targets_type = 'area'
        else:
            self.targets_type = 'normal'

    def has_nested(self):
        """Return true if this ability has nested abilities"""
        return (self.attack_subeffects is not None
                or self.subeffects is not None)

    def validate(self):
        super().validate()

        # make sure the ability has exactly one primary property
        primary_property_count = 0
        for property_name in type(self).primary_properties:
            if property_name in self.properties:
                primary_property_count += 1
                break
        if not primary_property_count:
            self.die("must have a primary property")
        if primary_property_count > 1:
            self.die("must have exactly one primary property")

        # here we check a bunch of weird edge cases

        # make sure that values which are not calculated for the root level
        # of abilities with subeffects are not present there
        if self.has_nested():
            for property_name in ['duration', 'dispellable']:
                if (property_name in self.properties
                        and self.properties[property_name] != type(self).default_properties.get(property_name)):
                    self.warn("has property '{0}' that should only be in its subeffects".format(property_name))

        # make sure that modifiers which should be positive are
        for property_name in type(self).primary_properties:
            if (property_name in self.properties
                    and self.get_modifier(property_name) <= 0):
                self.warn("has nonpositive property '{0}'".format(
                    property_name
                ))
        # also check that each subability is individually positive
        if self.subeffects is not None:
            for subeffect_properties in filter(None, self.subeffects):
                subability = self.create_nested(subeffect_properties)
                if subability.level() <= 0:
                    self.warn("has nonpositive subeffect with level {}".format(
                        subability.level()
                    ))
        # attack subeffects are also handled better below
        # this won't catch errors such as 'success' being < 3
        if self.attack_subeffects is not None:
            for property_name in ['critical success', 'effect', 'failure',
                                  'noncritical effect', 'success']:
                if self.attack_subeffects.get(property_name) is not None:
                    subability = self.create_nested(self.attack_subeffects[property_name])
                    if subability.level() <= 0:
                        self.warn("has nonpositive attack subeffect '{}' with level {}".format(
                            property_name,
                            subability.level()
                        ))

        # abilities with a duration must have something to apply
        # the duration to
        need_duration = (self.battlefield_effects is not None
                         or self.buffs is not None
                         or self.conditions is not None
                         or self.knowledge is not None)
        if (self.duration is not None
                and not need_duration):
            self.die("has duration with no purpose")

        # abilities that need a duration must have a duration
        if (self.duration is None
                and need_duration):
            self.die("is missing required property 'duration'")

        # abilities with targets = 'five' should not have small areas
        if (self.targets == 'five'
                and self.area is not None
                and self._area_modifier() <= 2):
            self.die("has too small of an area for targets='five'")

        # make sure that attack_subeffects has no extraneous keys
        if self.attack_subeffects is not None:
            for key in self.attack_subeffects:
                if key not in ['critical success', 'effect', 'failure',
                               'noncritical effect', 'success']:
                    self.warn("has unexpected key '{0}' in attack_subeffects".format(
                        key
                    ))

        # make sure that all of the levels of subabilities within
        # attack_subeffects make sense
        if self.attack_subeffects is not None:
            sublevels = self._calculate_attack_subability_levels()
            if 'success' in sublevels:
                level_modifier = sublevels['success'] - 3
            else:
                level_modifier = (
                    sublevels.get('effect', 0)
                    + sublevels.get('noncritical effect', 0)
                )

            # check whether the 'success' part is too low
            # after un-adding the 'effect' modifiers
            unmodified_success_modifier = (
                sublevels.get('success', 0)
                - sublevels.get('effect', 0)
                - sublevels.get('noncritical effect', 0)
                - 3
            )
            if ('success' in sublevels
                    and unmodified_success_modifier <= 0):
                self.warn("has success with nonpositive level {0}".format(
                    unmodified_success_modifier
                ))

            if ('failure' in sublevels
                    and not is_close(level_modifier - 3,
                                     sublevels['failure'])):
                self.warn("has failure with incorrect level {0} instead of {1}".format(
                    sublevels['failure'],
                    level_modifier - 3,
                ))

            if 'critical success' in sublevels and not is_close(
                    level_modifier + 9,
                    sublevels['critical success'],
            ):
                self.warn("has critical success with incorrect level {0} instead of {1}".format(
                    sublevels['critical success'],
                    level_modifier + 9,
                ))

        # "success" conditions and battlefield effects should only have one item
        # other item should be general effects, not success-only
        # unless they have a failure effect, which mimics 'effect' except for
        # the interaction with critical success
        if (self.attack_subeffects is not None
                and 'success' in self.attack_subeffects):
            success_effects = self.attack_subeffects['success']
            for t in ['conditions', 'battlefield effects']:
                if t in success_effects and len(success_effects[t]) > 1 and 'failure' not in sublevels:
                    self.warn("Has too many '{}': '{}'".format(t, success_effects[t]))
            if 'subeffects' in success_effects:
                self.warn("Should not have subeffects under success")

        # make sure that dispellable abilities have a reasonable duration
        if not self.dispellable and (self.duration is None
                                     or self.duration in ('round', 'concentration')):
            self.die("is not dispellable, but has trivial duration {0}".format(self.duration))

        # check for missing critical effects
        # but damaging spells don't need critical effects
        if (self.attack_subeffects is not None
                and 'critical success' not in self.attack_subeffects
                and 'damage' not in self.attack_subeffects.get('effect', {})):
            self.warn("is missing critical success")

        # immediate and swift effects should last until the end of
        # the round, not for 1 round
        if (self.duration == 'round'
                and (self.casting_time == 'immediate'
                     or self.casting_time == 'swift')):
            self.warn("should have duration 'end of round', not 'round'")

        # zones should not have brief duration
        if (self.duration == 'brief'
                and self.area_type == 'zone'):
            self.warn("should not have duration 'brief' with area type 'zone'")

    def level(self, ability_type=None):
        """Return the level of this ability.
        This calls all calculation functions relevant to the ability's properties.
        If ability_type is not None, modify the level to its in-game value for the given type"""
        try:
            level_modifier = {
                'class feature': -4,
                'magic item': -4,
                'spell': -4,
                None: 0,
            }[ability_type]
        except KeyError:
            raise Exception("Unrecognized ability type '{}'".format(ability_type))

        return super().level() + level_modifier

    def _area_modifier(self):
        modifier = RAW_MODIFIERS['area'][self.area_shape][self.area_size]

        modifier += RAW_MODIFIERS['area type'][self.area_type]

        # knowledge spells pay less for areas
        if self.knowledge is not None:
            return modifier / 2.0
        elif self.buffs is not None and self.targets == 'allies':
            # buff spells pay less for exceptionally large areas that target allies
            if modifier <= 2:
                return modifier
            else:
                return 2 + (modifier - 2) / 2.0
        else:
            return modifier

    def _attack_subeffects_modifier(self, show_warnings=True):

        # first, get the levels of all possible subabilities
        # we'll calculate the total level modifier using all of them
        sublevels = self._calculate_attack_subability_levels()

        # now that we have all the sublevels, determine the base level
        level_modifier = None
        # normally we determine the base level modifier from 'success'
        if 'success' in sublevels:
            level_modifier = sublevels['success'] - 3
        else:
            level_modifier = (
                sublevels.get('effect', 0)
                + sublevels.get('noncritical effect', 0)
            )

        return level_modifier

    def _battlefield_effects_modifier(self):
        modifier = 0

        for effect in self.battlefield_effects:
            try:
                modifier += RAW_MODIFIERS['battlefield effects'][effect]
            except KeyError:
                modifier += RAW_MODIFIERS['conditions'][effect]

        return modifier

    def _calculate_attack_subability_levels(self):
        sublevels = dict()

        for modifier_name in ['critical success', 'effect', 'failure',
                              'noncritical effect', 'success']:
            if self.attack_subeffects.get(modifier_name) is not None:
                subability = self.create_nested(
                    self.attack_subeffects[modifier_name]
                )
                sublevels[modifier_name] = subability.level()

        # adjust the sublevels to include shared effects
        if 'effect' in sublevels:
            if 'success' in sublevels:
                sublevels['success'] += sublevels['effect']
            if 'failure' in sublevels:
                sublevels['failure'] += sublevels['effect']
            if 'critical success' in sublevels:
                sublevels['critical success'] += sublevels['effect']

        if 'noncritical effect' in sublevels:
            if 'success' in sublevels:
                sublevels['success'] += sublevels['noncritical effect']
            if 'failure' in sublevels:
                sublevels['failure'] += sublevels['noncritical effect']

        return sublevels

    def _breakable_modifier(self):
        return RAW_MODIFIERS['breakable'][self.breakable]

    def _buffs_modifier(self):
        modifier = 0

        for buff in self.buffs:
            try:
                modifier += RAW_MODIFIERS['buffs'][buff]
            except TypeError:
                # the buff is a nested modifier
                top_level_name = list(buff)[0]
                value = buff[top_level_name]
                modifier += RAW_MODIFIERS['buffs'][top_level_name][value]

        return modifier

    def _casting_time_modifier(self):
        return RAW_MODIFIERS['casting time'][self.casting_time]

    def _conditions_modifier(self):
        modifier = 0
        for condition in self.conditions:
            modifier += RAW_MODIFIERS['conditions'][condition]
        return modifier

    def _choose_effect_modifier(self):
        return RAW_MODIFIERS['choose effect'][self.choose_effect]

    def _components_modifier(self):
        return RAW_MODIFIERS['components'][self.components]

    def _delay_effect_modifier(self):
        return RAW_MODIFIERS['delay effect'][self.delay_effect]

    def _damage_modifier(self):
        try:
            return RAW_MODIFIERS['damage'][self.damage]
        except TypeError:
            # the damage is a nested modifier
            top_level_name = list(self.damage)[0]
            value = self.damage[top_level_name]
            return RAW_MODIFIERS['damage'][top_level_name][value]

    def _dispellable_modifier(self):
        if self.dispellable:
            return 0
        # if the duration is effectively free, not being dispellable is useless
        elif self.duration is None or self._duration_modifier() <= 1:
            return 0
        # for normal durations, being dispellable doesn't matter much
        else:
            return int(self._duration_modifier() / 4) + 1

    def _duration_modifier(self):
        # if the duration only exists to be passed on to
        # subeffects, don't record a duration modifier here
        if self.duration_type == 'subeffect':
            return 0
        else:
            try:
                return RAW_MODIFIERS['duration'][self.duration_type][self.duration]
            except KeyError:
                self.die("has unrecognized duration '{}'".format(self.duration))

    def _expended_modifier(self):
        return RAW_MODIFIERS['expended'][self.expended]

    def _instant_effect_modifier(self):
        return RAW_MODIFIERS['instant effect'][self.instant_effect]

    def _knowledge_modifier(self):
        return RAW_MODIFIERS['knowledge'][self.knowledge]

    def _healing_modifier(self):
        try:
            return RAW_MODIFIERS['healing'][self.healing]
        except TypeError:
            # the healing is a nested modifier
            top_level_name = list(self.healing)[0]
            value = self.healing[top_level_name]
            return RAW_MODIFIERS['healing'][top_level_name][value]

    def _limit_affected_modifier(self):
        modifiers = RAW_MODIFIERS['limit affected']
        return modifiers[self.limit_affected_type][self.limit_affected]

    def _misc_modifier(self):
        return self.misc

    def _noncombat_modifier(self):
        # being noncombat has no direct effect on an ability's level
        # but some other calculations use it
        return 0

    def _range_modifier(self):
        if self.buffs is not None:
            return RAW_MODIFIERS['range']['buff'][self.range]
        else:
            return RAW_MODIFIERS['range']['normal'][self.range]

    def _repeatable_modifier(self):
        modifier = 0
        modifier += RAW_MODIFIERS['repeatable']['frequency'][
            self.repeatable['frequency']
        ]
        modifier += RAW_MODIFIERS['repeatable']['duration'][
            self.repeatable['duration']
        ]
        modifier += RAW_MODIFIERS['repeatable']['immediate'][
            self.repeatable.get('immediate', False)
        ]
        return modifier

    def _retry_failure_modifier(self):
        return RAW_MODIFIERS['retry failure'][self.retry_failure]

    def _shadow_modifier(self):
        return RAW_MODIFIERS['shadow'][self.shadow]

    def _shapeable_modifier(self):
        return RAW_MODIFIERS['shapeable'][self.shapeable]

    def _spell_resistance_modifier(self):
        return RAW_MODIFIERS['spell resistance'][self.spell_resistance]

    def _subeffects_modifier(self):
        modifier = 0
        for subeffect_properties in self.subeffects:
            subability = self.create_nested(subeffect_properties)
            modifier += subability.level()
        return modifier

    def _targets_modifier(self):
        if self.targets == 'automatically find one':
            if self.targets_type == 'area':
                # reduce the area cost by half
                return - self._area_modifier() / 2
            else:
                # double the range modifier
                return self._range_modifier()
        else:
            try:
                return RAW_MODIFIERS['targets'][self.targets_type][self.targets]
            except KeyError:
                self.die("has invalid targets '{}'".format(self.targets))

    def _teleport_modifier(self):
        modifier = 0
        modifier += RAW_MODIFIERS['teleport']['range'][
            self.teleport['range']
        ]
        modifier += RAW_MODIFIERS['teleport']['type'][
            self.teleport['type']
        ]
        modifier += RAW_MODIFIERS['teleport']['willing'][
            self.teleport['willing']
        ]
        return modifier

    def _trigger_modifier(self):
        modifier = 0
        modifier += RAW_MODIFIERS['trigger']['condition'][
            self.trigger['condition']
        ]
        modifier += RAW_MODIFIERS['trigger']['duration'][
            self.trigger['duration']
        ]
        return modifier
AbilityLeveler.import_config('content/ability_leveler_config.yaml')

def calculate_ability_levels(abilities, ability_type):
    levels = dict()
    for name in abilities:
        ability = AbilityLeveler(name, abilities[name])
        ability.validate()
        levels[name] = ability.level(ability_type)
    return levels

def main(args):
    if args['items']:
        abilities = util.import_yaml_file('content/magic_items.yaml')
        ability_type = 'magic item'
    elif args['rituals']:
        abilities = util.import_yaml_file('content/rituals.yaml')
        ability_type = 'spell'
    elif args['spells']:
        abilities = util.import_yaml_file('content/spells.yaml')
        ability_type = 'spell'
    elif args['class']:
        abilities = util.import_yaml_file('content/class_features.yaml')
        ability_type = 'class feature'
    elif args['feats']:
        abilities = util.import_yaml_file('content/feats.yaml')
        ability_type = 'class feature'
    else:
        raise Exception("I don't know what ability data to use")

    ability_levels = calculate_ability_levels(abilities, ability_type)
    for ability_name in sorted(ability_levels.keys()):
        print("{}: {}".format(
            ability_name,
            ability_levels[ability_name]
        ))

if __name__ == "__main__":
    main(docopt(doc))
