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
