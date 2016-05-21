#!/usr/bin/env python

import yaml

class Leveler:

    default_properties = list()
    meta_properties = list()
    possible_properties = list()
    recursive_properties = list()
    required_properties = list()

    @classmethod
    def import_config(cls, file_name):
        with open(file_name, 'r') as config_file:
            config = yaml.load(config_file)
            for key in config:
                python_key = key.replace(' ', '_')
                setattr(cls, python_key, config[key])

        # here we do some witchcraft to automatically add @properties to Leveler
        def create_leveler_property(property_name):
            def get_property(leveler):
                return leveler.properties.get(property_name, None)
            python_property_name = property_name.replace(' ', '_')
            setattr(cls, python_property_name, property(get_property))

        for property_name in cls.possible_properties:
            create_leveler_property(property_name)


    def __init__(self, name, properties):
        self.name = name
        self.properties = properties

        self._init_default_properties()
        self._init_derived_properties()

    def _init_default_properties(self):
        """Set default properties specified in Leveler.default_properties"""
        for property_name in type(self).default_properties:
            if self.properties.get(property_name) is None:
                self.properties[property_name] = type(self).default_properties[property_name]

    def _init_derived_properties(self):
        """Generate top-level properties that can be deduced from other properties"""
        # implemented by subclasses
        pass

    def get_modifier(self, property_name):
        """Get the level modifier for a given property

        Args:
            property_name (str)

        Yields:
            int
        """
        modifier_function_name = "_{0}_modifier".format(
            property_name.replace(' ', '_')
        )
        return getattr(self, modifier_function_name)()

    def validate(self):
        """Check for invalid properties, and warn or die appropriately"""
        if self.skip_validation:
            return

        # make sure there are no unrecognized properties
        for property_name in self.properties:
            if property_name not in type(self).possible_properties:
                self.die("has unknown property '{0}'".format(
                    property_name
                ))

        # make sure that all required properties are present
        for property_name in type(self).required_properties:
            if property_name not in self.properties:
                self.die("must have property '{0}'".format(
                    property_name
                ))

    def die(self, message):
        """Raise an exception that includes the name and properties of this leveler"""
        raise Exception("{0} {1} (properties: {2})".format(
            self,
            message,
            self.properties
        ))

    def warn(self, message):
        """Print a warning that includes the name and properties of this leveler"""
        print("Warning: {0} {1}".format(
            self,
            message
        ))

    def level(self):
        """Return the raw level of this object.
        This calls all calculation functions relevant to the object's properties"""
        level = 0

        # call all the calculation functions

        for property_name in self.properties:
            if (property_name not in type(self).meta_properties
                    and self.properties[property_name] is not None):
                level += self.get_modifier(property_name)

        return level

    def explain_level(self):
        """Print debugging information that explains this object's level"""
        print(self)
        for property_name in self.properties:
            # only explain non-default properties
            if (property_name in type(self).default_properties
                    and self.properties[property_name] == type(self).default_properties[property_name]):
                continue
            print("    {0}: {1}".format(
                property_name,
                self.get_modifier(property_name),
            ))

            # recursive properties should be explained individually
            if property_name in type(self).recursive_properties:
                for properties in self.properties[property_name]:
                    nested_leveler = self.create_nested(properties)
                    print("        nested: {0}".format(
                        nested_leveler.level()
                    ))
        print("total:", self.level())

    def __str__(self):
        return "Leveler('{0}')".format(self.name)

    def create_nested(self, properties):
        """Create a new leveler with the given properties
        The name of the leveler is based on this leveler's name

        Args:
            properties (dict)

        Yields:
            Leveler
        """
        return type(self)(self.name + '**nested', properties)
