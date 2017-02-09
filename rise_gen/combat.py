#!/usr/bin/env python

import argparse
from rise_gen.creature import Creature
from rise_gen.ability import Ability
import rise_gen.util as util
import cProfile
from pprint import pprint

class CreatureGroup(object):
    """A CreatureGroup is a group of creatures that acts like a single creature """
    # TODO: move dead creatures to the end of the array when they die

    def __init__(self, creatures):
        self.creatures = creatures

    def standard_attack(self, group):
        """Attack the given group of creatures

        Args:
            group (CreatureGroup): Creatures to attack
        """
        for c in self.creatures:
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
        return None

    def __str__(self):
        return 'CreatureGroup({})'.format([str(c) for c in self.creatures])


def run_combat(red, blue):
    """Simulate a round of combat between the given creatures

    Args:
        red (Creature): a creature that attacks first
        blue (Creature): a creature that attacks second
    """

    results = {
        'red is alive': 0,
        'blue is alive': 0,
        'rounds': 0
    }

    def run_combat_round():
        red.standard_attack(blue)
        blue.standard_attack(red)

        red.refresh_round()
        blue.refresh_round()
        results['rounds'] += 1

    while (red.is_alive() and blue.is_alive() and results['rounds'] <= 100):
        run_combat_round()

    if red.is_alive():
        results['red is alive'] += 1
    if blue.is_alive():
        results['blue is alive'] += 1

    red.refresh_combat()
    blue.refresh_combat()

    return results

def initialize_argument_parser():
    parser = argparse.ArgumentParser(
        description='Do battle between Rise creatures',
    )
    parser.add_argument(
        '-b', '--blue',
        dest='blue',
        help='creatures on the blue side',
        type=str,
        nargs='+',
    )
    parser.add_argument(
        '-t', '--test',
        dest='test',
        type=str,
        help='perform a specific test',
    )
    parser.add_argument(
        '-l', '--level',
        dest='level',
        help='the level of the characters',
        default=1,
        type=int,
    )
    parser.add_argument(
        '-p', '--print',
        dest='print',
        help='if true, print the generated characters',
        action='store_true',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        help='if true, print more output',
        action='store_true',
    )
    parser.add_argument(
        '--profile',
        dest='profile',
        help='if true, profile performance',
        nargs='?',
        type=str,
    )
    parser.add_argument(
        '-r', '--red',
        dest='red',
        help='creatures on the red side',
        type=str,
        nargs='+',
    )
    parser.add_argument(
        '--trials',
        default=1000,
        dest='trials',
        help='The number of trials to run',
        type=int,
    )
    parser.add_argument(
        '--bl',
        dest='blue level',
        help='level of creatures on the blue side',
        type=int,
    )
    parser.add_argument(
        '--rl',
        dest='red level',
        help='level of creatures on the red side',
        type=int,
    )
    return vars(parser.parse_args())

def custom_red_modifications(red):
    """Modify the CreatureGroup for random testing

    Args:
        red (CreatureGroup): Group of red creatures
    """
    # for c in red.creatures:
    #     c.add_ability(Ability.by_name('critical threshold'))
    pass

def custom_blue_modifications(blue):
    """Modify the CreatureGroup for random testing

    Args:
        blue (CreatureGroup): Group of blue creatures
    """
    # for c in blue.creatures:
    #     c.add_ability(Ability.by_name('mighty blows'))
    pass

def generate_combat_results(red, blue, trials):
    raw_results = list()

    for t in range(trials):
        raw_results.append(run_combat(red, blue))

    results = {
        'red alive %': int([
            True if result['red is alive'] else False
            for result in raw_results
        ].count(True) / float(trials) * 100),
        'blue alive %': int([
            True if result['blue is alive'] else False
            for result in raw_results
        ].count(True) / float(trials) * 100),
        'average rounds': sum([results['rounds'] for results in raw_results]) / float(trials)
    }

    return results

def test_training_dummy(level, trials):
    sample_creature_names = util.import_yaml_file('content/sample_creatures.yaml').keys()
    # strip out the templates and non-creature stuff
    sample_creature_names = list(filter(
        lambda name: name.upper() != name,
        sample_creature_names,
    ))
    # remove the dummy, which shouldn't fight itself
    sample_creature_names.pop(sample_creature_names.index('dummy'))
    sample_creatures = list()
    for name in sample_creature_names:
        try:
            sample_creatures.append(Creature.from_sample_creature(name, level=level))
        except Exception as e:
            print(e)
    training_dummy = Creature.from_sample_creature('dummy', level=level)

    results = dict()

    for creature in sample_creatures:
        for i in range(trials):
            rounds_to_defeat_dummy = run_combat(creature, training_dummy)['rounds']
            try:
                results[creature.name] += rounds_to_defeat_dummy
            except KeyError:
                results[creature.name] = rounds_to_defeat_dummy
        results[creature.name] /= trials

    for key in results.keys():
        results[key] = round(results[key], 1)

    pprint(results)

def generate_creature_groups(args):
    blue_creatures = [Creature.from_sample_creature(
        name,
        level=args['blue level'] or args['level']
    ) for name in args['blue']]
    blue = CreatureGroup(blue_creatures)

    red_creatures = [Creature.from_sample_creature(
        name,
        level=args['red level'] or args['level']
    ) for name in args['red']]
    red = CreatureGroup(red_creatures)

    return blue, red

def main(args):

    blue, red = generate_creature_groups(args)

    custom_blue_modifications(blue)
    custom_red_modifications(red)

    if args.get('verbose'):
        print("RED:\n{}\nBLUE:\n{}".format(red, blue))

    pprint(generate_combat_results(red, blue, args['trials']))

if __name__ == "__main__":
    cmd_args = initialize_argument_parser()
    if cmd_args.get('profile'):
        cProfile.run('main(cmd_args)', sort=cmd_args.get('profile'))
    elif cmd_args.get('test') == 'dummy':
        test_training_dummy(
            level=cmd_args['level'],
            trials=100
        )
    elif cmd_args.get('test') == 'levels':
        cmd_args['trials'] //= 2
        for i in range(1, 21):
            cmd_args['level'] = i
            print(str(i) + ": ", end="")
            main(cmd_args)
    elif cmd_args.get('test') == 'accuracy':
        blue, red = generate_creature_groups(cmd_args)
        print("blue", blue.get_accuracy(red, cmd_args['trials']))
        print("red", red.get_accuracy(blue, cmd_args['trials']))
    elif cmd_args.get('test') == 'level_diff':
        cmd_args['trials'] //= 10
        for i in range(3, 21):
            cmd_args['blue level'] = i
            cmd_args['red level'] = i-2
            print(str(i) + ": ", end="")
            main(cmd_args)
    else:
        main(cmd_args)
