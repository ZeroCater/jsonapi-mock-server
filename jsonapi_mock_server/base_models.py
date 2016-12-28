from collections import OrderedDict
import copy
import inflection
import os

from django.conf import settings
from utils import upper_camelize_resource


class BaseResource(object):
    resource_type = ""
    attributes = {}
    fake_attributes = {}
    attribute_metadata = {}
    relationship_metadata = {}
    # The json_api_rules attribute provides a hook from resource to JsonAPIBuilder,
    # allowing us to specify exceptions or special rules to apply when creating
    # a particular JsonAPI resource object.
    json_api_rules = []
    relationships = []
    page_size = settings.MS_PAGE_SIZE

    type_lookup = {
        str: "String",
        type(None): "String",
        int: "Integer",
        bool: "Boolean",
        list: "List",
    }

    relation_type_lookup = {
        tuple: "ManyToMany",
        int: "OneToMany",
        str: "OneToMany",
    }

    def get_attributes(self):
        return copy.deepcopy(self.attributes)

    def get_fake_attributes(self):
        fake_attributes = {}
        for attribute, fake in self.fake_attributes.iteritems():
            fake_attributes[attribute] = fake.generate_value()
        return fake_attributes

    def get_field_label(self, attribute):
        return inflection.titleize(attribute)

    def get_action_metadata(self):
        attributes = {}
        for fieldname, value in self.attributes.iteritems():
            field_info = OrderedDict()
            field_info['type'] = self.type_lookup[type(value)]
            field_info['required'] = False
            field_info['read_only'] = False
            field_info['label'] = self.get_field_label(fieldname)
            field_info['choices'] = []

            if field_info['type'] == 'List':
                field_info['child'] = {
                    'choices': [{ 'value': 'value', 'display_name': 'display_name' } for x in range(3)]
                }

            field_metadata = self.attribute_metadata.get(fieldname, {})
            field_info.update(field_metadata)

            attributes[inflection.underscore(fieldname)] = field_info

        for relationship in self.relationships:
            fieldname, value = relationship

            field_info = OrderedDict()
            field_info['initial'] = []
            field_info['type'] = 'Relationship'
            field_info['relationship_type'] = self.relation_type_lookup[type(value)]
            field_info['relationship_resource'] = upper_camelize_resource(fieldname)
            field_info['allows_include'] = True
            field_info['required'] = False
            field_info['read_only'] = False
            field_info['label'] = self.get_field_label(fieldname)

            field_metadata = self.relationship_metadata.get(fieldname, {})
            field_info.update(field_metadata)

            attributes[inflection.underscore(fieldname)] = field_info

        return attributes

    def find_relationship_id(related_type):
        for relationship in self.relationships:
            if relationship[0].lower == related_type.lower():
                return relationship[1]
        return None
