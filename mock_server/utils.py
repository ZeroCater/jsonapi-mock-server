import importlib
import inflection
import sys


def upper_camelize_resource(resource_type):
    return inflection.camelize(inflection.singularize(resource_type), uppercase_first_letter=True)

def camelize_resource(resource_type):
    return inflection.camelize(inflection.singularize(resource_type))

def underscore_resource(resource_type):
    return inflection.underscore(inflection.pluralize(resource_type))

def get_instance_of_resource(resource_type):
    resource_module_str = inflection.underscore(resource_type)
    module = importlib.import_module('resources.'+resource_module_str)
    class_ = getattr(module, resource_type+"Resource")
    instance = class_()
    return instance
