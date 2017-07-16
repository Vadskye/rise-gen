#!/usr/bin/env python3

from rise_gen.rise_data import ATTRIBUTES, SKILLS

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
