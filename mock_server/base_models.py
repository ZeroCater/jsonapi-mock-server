import copy
import os


class BaseResource(object):
    resource_type = ""
    attributes = {}
    fake_attributes = {}
    # The json_api_rules attribute provides a hook from resource to JsonAPIBuilder,
    # allowing us to specify exceptions or special rules to apply when creating
    # a particular JsonAPI resource object.
    json_api_rules = []
    relationships = []
    page_size = int(os.environ.get('DEFAULT_PAGE_SIZE'))

    def get_attributes(self):
        return copy.deepcopy(self.attributes)

    def get_fake_attributes(self):
        fake_attributes = {}
        for attribute, fake in self.fake_attributes.iteritems():
            fake_attributes[attribute] = fake.generate_value()
        return fake_attributes

    def find_relationship_id(related_type):
        for relationship in self.relationships:
            if relationship[0].lower == related_type.lower():
                return relationship[1]
        return None
