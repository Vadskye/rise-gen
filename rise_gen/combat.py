#!/usr/bin/env python3

import argparse
# from rise_gen.ability import Ability
from rise_gen.creature import Creature
from rise_gen.creature_group import CreatureGroup
from rise_gen.output import format_results
import rise_gen.util as util
import cProfile
from pprint import pprint, pformat


def run_combat(red, blue):
    """Simulate a round of combat between the given creatures

    Args:
        red (Creature): a creature that attacks first
        blue (Creature): a creature that attacks second
    """

    red.refresh_combat()
    blue.refresh_combat()

    results = {
        'red is alive': 0,
        'red all alive': 0,
        'blue is alive': 0,
        'blue all alive': 0,
        'rounds': 0
    }

    def run_combat_round():
        red.standard_attack(blue)
        blue.standard_attack(red)

        red.refresh_round()
        blue.refresh_round()
        results['rounds'] += 1

    i = 0
    any_creatures_acted = True
    while any_creatures_acted:
        any_creatures_acted = any_creatures_acted and red.take_extra_round(i, blue)
        any_creatures_acted = any_creatures_acted and blue.take_extra_round(i, red)
        i += 1

    while (red.is_alive() and blue.is_alive() and results['rounds'] <= 100):
        run_combat_round()

    if red.is_alive():
        results['red is alive'] += 1
    if red.all_alive():
        results['red all alive'] += 1
    if blue.is_alive():
        results['blue is alive'] += 1
    if blue.all_alive():
        results['blue all alive'] += 1

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
        help='if provided, profile performance',
        action='store_true',
    )
    parser.add_argument(
        '--profilesort',
        dest='profilesort',
        default='tottime',
        help='Sort function for profiling data',
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
    for c in red.creatures:
        # c.add_ability('overwhelmed')
        # c.add_ability('buff/damage')
        # c.add_ability('extra round')
        pass


def custom_blue_modifications(blue):
    """Modify the CreatureGroup for random testing

    Args:
        blue (CreatureGroup): Group of blue creatures
    """
    for c in blue.creatures:
        # c.add_ability('overwhelmed')
        # c.add_ability('buff/accuracy')
        # c.add_ability('extra round')
        pass


def generate_combat_results(red, blue, trials):
    raw_results = list()

    for t in range(trials):
        raw_results.append(run_combat(red, blue))

    trials_modifier = float(trials) / 100

    results = {
        'red win %': int(round([
            True if result['red is alive'] else False
            for result in raw_results
        ].count(True) / trials_modifier, -1)),
        'red all %': int(round([
            True if result['red all alive'] else False
            for result in raw_results
        ].count(True) / trials_modifier, -1)),
        'blue win %': int(round([
            True if result['blue is alive'] else False
            for result in raw_results
        ].count(True) / trials_modifier, -1)),
        'blue all %': int(round([
            True if result['blue all alive'] else False
            for result in raw_results
        ].count(True) / trials_modifier, -1)),
        'rounds': round(sum([results['rounds'] for results in raw_results]) / float(trials), 1)
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
    training_dummy = CreatureGroup([Creature.from_sample_creature('dummy', level=level)])

    results = dict()

    for creature in sample_creatures:
        for i in range(trials):
            rounds_to_defeat_dummy = run_combat(
                CreatureGroup([creature]),
                training_dummy
            )['rounds']
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
        level=args.get('blue level') or args.get('level')
    ) for name in args['blue']]
    blue = CreatureGroup(blue_creatures)

    red_creatures = [Creature.from_sample_creature(
        name,
        level=args.get('red level') or args.get('level')
    ) for name in args['red']]
    red = CreatureGroup(red_creatures)

    custom_blue_modifications(blue)
    custom_red_modifications(red)

    return blue, red


def run_test(test, args):
    if test == 'dummy':
        test_training_dummy(
            level=args['level'],
            # TODO: use a different default instead of dividing here
            trials=args['trials'] // 10,
        )
    elif test == 'doubling':
        args['trials'] //= 2
        level_diff = 2
        results = []
        for i in range(1 + level_diff, 21):
            args['red level'] = i
            args['blue level'] = i - level_diff
            results.append(main(args))
            results[-1]['level'] = i
        print(format_results(results))
    elif test == 'levels':
        args['trials'] //= 2
        results = []
        for i in range(1, 21):
            args['level'] = i
            results.append(main(args))
            results[-1]['level'] = i
        print(format_results(results))
    elif test == 'criticals':
        args['trials'] //= 2
        for i in range(1, 21):
            args['level'] = i
            blue, red = generate_creature_groups(args)
            criticals = {'blue': 0, 'red': 0}
            for t in range(args['trials']):
                results = run_combat(red, blue)
                criticals['blue'] += (
                    sum([c.critical_hits for c in blue.creatures])
                    / len(blue.creatures) / results['rounds']
                )
                criticals['red'] += (
                    sum([c.critical_hits for c in red.creatures])
                    / len(red.creatures) / results['rounds']
                )
            criticals['blue'] /= args['trials']
            criticals['red'] /= args['trials']
            formatted_criticals = pformat(criticals)
            print(f"{i} crits/round: {formatted_criticals}")
    elif test == 'accuracy':
        results = []
        for i in range(1, 21):
            args['level'] = i
            blue, red = generate_creature_groups(args)
            results.append({
                'level': i,
                'blue accuracy': blue.get_accuracy(red, args['trials']),
                'red accuracy': red.get_accuracy(blue, args['trials']),
            })
        print(format_results(results))
    elif test == 'doubling_accuracy':
        level_diff = 2
        results = []
        for i in range(1 + level_diff, 21):
            args['red level'] = i
            args['blue level'] = i - level_diff
            blue, red = generate_creature_groups(args)
            results.append({
                'level': i,
                'blue accuracy': blue.get_accuracy(red, args['trials']),
                'red accuracy': red.get_accuracy(blue, args['trials']),
            })
        print(format_results(results))
    elif test == 'level_diff':
        args['trials'] //= 10
        for i in range(3, 21):
            args['blue level'] = i
            args['red level'] = i - 2
            print(str(i) + ": ", end="")
            main(args)


def main(args):

    blue, red = generate_creature_groups(args)

    if args.get('verbose'):
        print("RED:\n{}\nBLUE:\n{}".format(red, blue))

    filtered_results = generate_combat_results(red, blue, args['trials'])

    # these are unnecessary if only one creature is in the group
    if len(blue.creatures) == 1:
        filtered_results.pop('blue all %')
    if len(red.creatures) == 1:
        filtered_results.pop('red all %')

    return filtered_results


if __name__ == "__main__":
    cmd_args = initialize_argument_parser()
    if cmd_args.get('profile'):
        if (cmd_args.get('profilesort')):
            cProfile.run('main(cmd_args)', sort=cmd_args.get('profilesort'))
        else:
            cProfile.run('main(cmd_args)')
    elif cmd_args.get('test'):
        run_test(cmd_args['test'], cmd_args)
    else:
        print(main(cmd_args))
