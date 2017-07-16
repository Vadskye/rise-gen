#!/usr/bin/env python3

class CreatureGroup(object):
    """A CreatureGroup is a group of creatures that acts like a single creature """
    # TODO: move dead creatures to the end of the array when they die

    def __init__(self, creatures):
        self.creatures = creatures

    def take_extra_round(self, round_number, group):
        """For each creature in this group who can act during extra rounds, have them act for the given round.

        Args:
            round_number (int): Round to act for
            group (CreatureGroup): Creatures to attack

        Yields:
            bool: True if any creatures in this group acted, False otherwise
        """
        any_creatures_acted = False
        for c in self.creatures:
            if round_number < c.extra_rounds and c.is_alive():
                any_creatures_acted = True
                for i in range(c.action_count):
                    target = group.get_living_creature()
                    # if all targets are dead, stop attacking
                    if target is None:
                        return
                    else:
                        c.standard_attack(target)
        return any_creatures_acted

    def standard_attack(self, group):
        """Attack the given group of creatures

        Args:
            group (CreatureGroup): Creatures to attack
        """
        for c in self.creatures:
            if not c.is_alive():
                continue
            for i in range(c.action_count):
                target = group.get_living_creature()
                # if all targets are dead, stop attacking
                if target is None:
                    return
                else:
                    c.standard_attack(target)

    def get_accuracy(self, group, trials):
        """Test the average accuracy against the given group"""
        hits = 0
        misses = 0
        for i in range(trials):
            for creature in self.creatures:
                for target in group.creatures:
                    if creature.check_hit(target):
                        hits += 1
                    else:
                        misses += 1
        return hits / (hits + misses)

    def get_living_creature(self):
        """Return a single living creature

        Yields:
            Creature: living creature
        """
        for c in self.creatures:
            if c.is_alive():
                return c
        return None

    def refresh_round(self):
        """Refresh the round for all creatures in the group"""
        for c in self.creatures:
            c.refresh_round()

    def refresh_combat(self):
        """Refresh the combat for all creatures in the group"""
        for c in self.creatures:
            c.refresh_combat()

    def is_alive(self):
        """Check whether any creatures in the group are alive

        Yields:
            bool: True if any creatures are alive, false otherwise
        """
        for c in self.creatures:
            if c.is_alive():
                return True
        return False

    def all_alive(self):
        """Check whether all creatures in the group are alive

        Yields:
            bool: True if all creatures are alive, false otherwise
        """
        for c in self.creatures:
            if not c.is_alive():
                return False
        return True

    def __str__(self):
        return 'CreatureGroup({})'.format([str(c) for c in self.creatures])
