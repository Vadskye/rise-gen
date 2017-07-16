#!/usr/bin/env python3
import re

from rise_gen.ability import get_ability_definitions


class Ability:

    ability_definitions = None

    def __init__(
        self,
        name,
        effects=None,
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
        """Create an Ability by its name"""
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
