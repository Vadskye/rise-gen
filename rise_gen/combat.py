#!/usr/bin/env python

import argparse
from rise_gen.creature import get_sample_creature
import cProfile
from pprint import pprint

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
        help='the level of the character',
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
    )
    parser.add_argument(
        '--trials',
        default=10000,
        dest='trials',
        help='The number of trials to run',
        type=int,
    )
    return vars(parser.parse_args())

def custom_red_modifications(red):
    red.level = 14
    red.clear_cache()
    pass
    # red.add_ability('heartseeker')
    # red.add_ability('critical multiplier')

def custom_blue_modifications(blue):
    pass
    # blue.add_ability('extra attack')

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
    sample_creature_names = 'barbarian barbarian_greatsword cleric cleric_spells druid druid_spells fighter fighter_dex ranger rogue rogue_str sorcerer warrior warrior_dex warrior_str_dex wizard'.split()
    sample_creatures = [get_sample_creature(name, level=level) for name in sample_creature_names]
    training_dummy = get_sample_creature('dummy', level=level)

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


def main(args):
    red = get_sample_creature(args['red'], level=args.get('level'))
    custom_red_modifications(red)
    blue = get_sample_creature(args['blue'], level=args.get('level'))
    custom_blue_modifications(blue)

    if args.get('verbose'):
        print("RED:\n{}\nBLUE:\n{}".format(red, blue))

    print(generate_combat_results(red, blue, args['trials']))

if __name__ == "__main__":
    cmd_args = initialize_argument_parser()
    if cmd_args.get('profile'):
        cProfile.run('main(cmd_args)', sort=cmd_args.get('profile'))
    elif cmd_args.get('test') == 'dummy':
        test_training_dummy(
            level=cmd_args.get('level', 1),
            trials=100
        )
    elif cmd_args.get('test') == 'levels':
        cmd_args['trials'] /= 10
        for i in range(1, 21):
            cmd_args['level'] = i
            print(str(i) + ":",)
            main(cmd_args)
    else:
        main(cmd_args)
