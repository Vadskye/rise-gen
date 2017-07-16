#!/usr/bin/env python3

from rise_gen.abilities.ability_effect import AbilityEffect


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
