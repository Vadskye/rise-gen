#!/usr/bin/env python3
from rise_gen.dice import Die
from rise_gen.output import format_results

def standard_damage(level):
    die = Die(size=8, count=1)
    die.increase_size(level // 2)
    return die.average()


def aoe_damage(level):
    die = Die(size=4, count=1)
    die.increase_size(level // 2)
    return die.average()


def main():
    results = []
    for level in range(1, 31):
        r = {
            'level': level,
            'std': standard_damage(level),
            'aoe': aoe_damage(level),
        }
        r['ratio'] = r['std'] / r['aoe']
        results.append(r)
    print(format_results(results))


if __name__ == "__main__":
    main()
