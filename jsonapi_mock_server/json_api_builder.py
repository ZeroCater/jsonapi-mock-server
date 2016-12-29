import inflection
from math import ceil

from utils import camelize_resource, underscore_resource, upper_camelize_resource, get_instance_of_resource


class JsonAPIBuilder(object):
    def __init__(self, request):
        super(JsonAPIBuilder, self).__init__()
        self.request = request
        self.origin = "{}://{}".format(request.scheme, request.META.get('HTTP_HOST'))
        self.url = "{}{}".format(self.origin, self.request.path)


class JsonAPIErrorBuilder(JsonAPIBuilder):
    def __init__(self, request, *args, **kwargs):
        super(JsonAPIErrorBuilder, self).__init__(request)

    def build_401_error_object(self):
        error_msg = "Authentication credentials were not provided."
        return {
            "errors": [ self._build_error_object(status="401", error_msg=error_msg) ]
        }

    def _build_error_object(self, status="400", pointer=None, error_msg="Error message."):
        return {
            "status": status,
            "source": {
                "pointer": pointer if pointer else "/data"
            },
            "detail": error_msg
        }

    def build_error_list_object(self, attribute_errors):
        return {
            "errors": map(
                lambda attr: self._build_error_object(status="400", pointer="/data/attributes/{}".format(attr)),
                attribute_errors
            )
        }


class JsonAPIResourceDetailBuilder(JsonAPIBuilder):
    def __init__(self, request, resource_type, resource_id, config=None):
        super(JsonAPIResourceDetailBuilder, self).__init__(request)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_instance = get_instance_of_resource(resource_type)
        self.relationships = self.resource_instance.relationships
        self.json_api_rules = self.resource_instance.json_api_rules
        self.attributes = self.get_resource_attributes(self.resource_instance, config)

    def get_resource_attributes(self, resource_instance, config):
        attributes = resource_instance.get_attributes()

        disable_fake_data = bool(config and not config.get('fake', True))
        if not disable_fake_data:
            attributes.update(resource_instance.get_fake_attributes())

        if 'attributes' in config:
            attributes.update(config['attributes'])

        return attributes


    def build_resource_detail_object(self):
        resource_detail_object = {
            "data": {
                "type": self.resource_type,
                "id": str(self.resource_id),
                "attributes": self.attributes,
                "links": self._build_self_links_object()
            }
        }

        if 'exclude_resource_object_link' in self.json_api_rules:
           del resource_detail_object["data"]["links"]

        relationships_object = self._build_relationships_object()
        if relationships_object:
            resource_detail_object["data"].update({"relationships": relationships_object})

        return resource_detail_object


    def _build_self_links_object(self):
        resource_type_for_url = underscore_resource(self.resource_type)
        return {
            "self": "{}/{}/{}".format(self.origin, resource_type_for_url, self.resource_id)
        }

    def _build_relationship_data(self, related_id, related_type):
        related_type_as_type = upper_camelize_resource(related_type)
        return {
            "id": str(related_id),
            "type": related_type_as_type
        }

    def _build_m2m_relationship_object(self, related_ids, related_type):
        resource_type_for_url = underscore_resource(self.resource_type)
        related_type_for_url = underscore_resource(related_type)
        related_link = "{}/{}/{}/{}".format(self.origin,
                                            resource_type_for_url,
                                            self.resource_id,
                                            related_type_for_url)
        self_link = "{}/{}/{}/relationships/{}".format(self.origin,
                                                       resource_type_for_url,
                                                       self.resource_id,
                                                       related_type_for_url)

        return {
            related_type: {
                "data": [self._build_relationship_data(related_id, related_type)
                         for related_id in related_ids],
                "links": {
                    "related": related_link,
                    "self": self_link
                },
                "meta": {
                    "count": len(related_ids)
                }
            }
        }

    def _build_m2one_relationship_object(self, related_id, related_type):
        resource_type_for_url = underscore_resource(self.resource_type)
        related_type_for_url = underscore_resource(related_type)
        related_link = "{}/{}/{}".format(self.origin,
                                         related_type_for_url,
                                         related_id)
        self_link = "{}/{}/{}/relationships/{}".format(self.origin,
                                                       resource_type_for_url,
                                                       self.resource_id,
                                                       related_type_for_url)

        return {
            related_type: {
                "data": self._build_relationship_data(related_id, related_type),
                "links": {
                    "related": related_link,
                    "self": self_link
                }
            }
        }

    def _build_relationships_object(self):
        relationships_object = {}

        for related_type, related_ids in self.relationships:
            is_m2m_relationship = (type(related_ids) in (tuple, list))
            if is_m2m_relationship:
                relationship = self._build_m2m_relationship_object(related_ids, related_type)
            else:
                relationship = self._build_m2one_relationship_object(related_ids, related_type)
            relationships_object.update(relationship)

        return relationships_object

class JsonAPIResourceListBuilder(JsonAPIBuilder):
    def __init__(self, request, resource_type, page_size, length, config=None, curr_page=1):
        super(JsonAPIResourceListBuilder, self).__init__(request)
        self.resource_type = camelize_resource(resource_type)
        self.curr_page = curr_page
        self.page_size = page_size
        self.length = length
        self.num_pages = int(ceil(self.length/(self.page_size*1.0)))
        self.config = config

        try:
            self.resource_instance = get_instance_of_resource(resource_type)
            self.json_api_rules = self.resource_instance.json_api_rules
        except:
            self.json_api_rules = None

        ids_range_start = ((self.curr_page-1) * self.page_size) + 1
        ids_range_end = (ids_range_start + self.page_size) if self.curr_page < self.num_pages else (self.length + 1)
        self.resource_ids = range(ids_range_start, ids_range_end)
        if self.config.get('filter') and 'id' in self.config['filter'].keys():
            self.resource_ids = self.config['filter']['id']

    def build_resource_list_object(self):
        resource_list_object = {
            "data": self._build_resource_list_data(),
            "links": self._build_list_links_object(),
            "meta": self._build_list_meta_object()
        }

        if 'exclude_list_links' in self.json_api_rules:
           del resource_list_object["links"]

        if 'exclude_list_meta' in self.json_api_rules:
           del resource_list_object["meta"]

        return resource_list_object

    def build_include_list(self):
        return self._build_resource_list_data()

    def _build_resource_list_data(self):
        resource_list_data = []
        for resource_id in self.resource_ids:
            resource_detail_builder = JsonAPIResourceDetailBuilder(self.request,
                                                                   self.resource_type,
                                                                   resource_id,
                                                                   config=self.config)
            resource_list_data.append(resource_detail_builder.build_resource_detail_object())

        resource_list_data = [resource_obj['data'] for resource_obj in resource_list_data]
        return resource_list_data

    def _build_list_links_object(self):
        resource_type_for_url = underscore_resource(self.resource_type)
        next_page = self.curr_page+1 if self.num_pages > 0 and self.curr_page < self.num_pages else None
        prev_page = self.curr_page-1 if self.num_pages > 0 and self.curr_page > 0 else None

        return {
            "first": "{}?page=1".format(self.url),
            "last": "{}?page={}".format(self.url, self.num_pages),
            "next": "{}?page={}".format(self.url, next_page) if next_page else None,
            "prev": "{}?page={}".format(self.url, prev_page) if prev_page else None,
            "self": "{}/{}".format(self.origin, resource_type_for_url)
        }

    def _build_list_meta_object(self):
        return {
            "pagination": {
                "count": self.length,
                "page": 1,
                "pages": self.num_pages
            }
        }


class JsonAPIIncludedResourceListBuilder(JsonAPIResourceListBuilder):
    def __init__(self, request, resource_type, resource_ids, page_size, length, config=None, curr_page=1):
        super(JsonAPIIncludedResourceListBuilder, self).__init__(
            request, resource_type, page_size, length, config=config)
        self.resource_ids = resource_ids
