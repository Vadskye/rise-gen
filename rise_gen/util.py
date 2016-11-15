#!/usr/bin/env python

import yaml

def import_yaml_file(file_name):
    with open(file_name, 'r') as yaml_file:
        data = yaml.load(yaml_file)

        # handle $ref inheritance
        for key in data:
            inheritance_levels = 0
            if isinstance(data[key], dict):
                while '$ref' in data[key]:
                    parent_name = data[key]['$ref']
                    parent = data.get(parent_name)

                    # if that fails, check TEMPLATES
                    if parent is None:
                        parent = data.get('TEMPLATES', dict()).get(parent_name)

                    # if that also fails, give up
                    if parent is None:
                        raise Exception(
                            "Undefined $ref to parent '{0}'".format(parent_name)
                        )

                    new_thing = parent.copy()
                    new_thing.update(data[key])
                    if '$ref' in parent:
                        # make sure we don't infinite loop
                        if parent['$ref'] == data[key]['$ref']:
                            raise Exception("Key '{}' has looping inheritance".format(
                                key
                            ))
                        else:
                            new_thing['$ref'] = parent['$ref']
                            inheritance_levels += 1
                            if inheritance_levels > 1000:
                                raise Exception("Key '{}' has looping inheritance".format(
                                    key
                                ))
                    else:
                        # remove the ref if the parent doesn't also have a $ref
                        # if it does, we need to go through another level of inheritance
                        del new_thing['$ref']
                    data[key] = new_thing

        # strip TEMPLATES
        # TODO: use a config file for this
        data.pop('TEMPLATES', None)

        return data

_number_words = {
    0: 'zero',
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
    6: 'six',
    7: 'seven',
    8: 'eight',
    9: 'nine',
    10: 'ten',
    11: 'eleven',
    12: 'twelve',
    13: 'thirteen',
    14: 'fourteen',
    15: 'fifteen',
    16: 'sixteen',
    17: 'seventeen',
    18: 'eighteen',
    19: 'nineteen',
    20: 'twenty',
}
def num_to_word(n):
    if n >= 20:
        raise Exception("num_to_word yet supported for n > 20")
    elif n < 0:
        raise Exception("num_to_word yet supported for negative n")
    return _number_words[n]
