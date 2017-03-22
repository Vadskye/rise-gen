#!/usr/bin/env python3

import random
import re

class Die(object):
    def __init__(self, size, count=1):
        self.count = count
        self.size = size

    def average(self):
        total = 0
        for i in range(self.count):
            total += (1 + self.size) / 2.0
        return total

    def maximum(self):
        return self.size * self.count

    def roll(self):
        total = 0
        for i in range(self.count):
            total += random.randrange(1, self.size + 1)
        return total

    # adding and subtracting from a Die increases the die size
    # this includes wrapping at d10 into 2d6
    def __add__(self, value):
        new_die = Die(size=self.size, count=self.count)
        # value is the number of size changes
        if value >= 0:
            for i in range(value):
                new_die.increase_size()
        else:
            for i in range(-value):
                new_die.decrease_size()
        return new_die

    def __sub__(self, value):
        new_die = Die(size=self.size, count=self.count)
        # value is the number of size decreases
        if value >= 0:
            for i in range(value):
                new_die.decrease_size()
        else:
            for i in range(-value):
                new_die.increase_size()
        return new_die

    def increase_size(self):
        if self.size <= 3:
            self.size += 1
        elif self.size <= 8:
            self.size += 2
        elif self.size == 10:
            self.size = 6
            self.count *= 2
        else:
            raise Exception("Impossible die size")

    def decrease_size(self):
        if self.size <= 1:
            pass
        elif self.size <= 4 and self.count == 1:
            self.size -= 1
        elif self.size == 6 and self.count > 1:
            self.size = 10
            self.count /= 2
        elif self.size <= 10:
            self.size -= 2
        else:
            raise Exception("Impossible die size")

    #read a single collection of dice, like '2d6'
    @classmethod
    def from_string(cls, die_name):
        # First check the number of dice
        # http://stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings
        die_split = list(filter(bool, re.split('d', die_name)))
        if len(die_split)>1:
            count = int(die_split[0])
            size = int(die_split[1])
        else:
            count = 1
            size = int(die_split[0])
        #Extract the die size
        return cls(size=size, count=count)

    def __repr__(self):
        text = 'Die({0}d{1})'.format(self.count, self.size)
        return text

    def __str__(self):
        text = '{0}d{1}'.format(self.count, self.size)
        return text

    def __eq__(self, die):
        return self.size == die.size and self.count == die.count

class DieCollection(object):
    def __init__(self, *args):
        self.dice = list(args)

    def roll(self):
        total = 0
        for die in self.dice:
            total += die.roll()
        return total

    def average(self):
        total = 0
        for die in self.dice:
            total += die.average()
        return total

    def maximum(self):
        total = 0
        for die in self.dice:
            total += die.maximum()
        return total

    def add_die(self, die):
        self.dice.append(die)

    def remove_die(self, die):
        try:
            self.dice.pop(self.dice.index(die))
        except IndexError:
            # no matching die found
            pass

    def resize_die(self, i, steps):
        self.dice[i] += steps

    def resize_dice(self, steps):
        """Resize all dice in this collection"""
        for i, die in enumerate(self.dice):
            self.dice[i] += steps

    def increase_size(self):
        for die in self.dice:
            die.increase_size()

    def decrease_size(self):
        for die in self.dice:
            die.decrease_size()

    def __repr__(self):
        return 'DieCollection({0})'.format(
            ', '.join([str(die) for die in self.dice])
        )

    def __str__(self):
        return '+'.join([str(die) for die in self.dice])

    def __eq__(self, die_collection):
        # for now, compare in order, even though that's not technically correct
        for i in range(len(self.dice)):
            if self.dice[i] != die_collection.dice[i]:
                return False
        return True

d20 = Die(20)
