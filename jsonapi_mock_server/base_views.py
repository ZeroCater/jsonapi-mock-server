import json
import re

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from inflection import camelize, pluralize, singularize
from rest_framework import viewsets

from hooks import MockServerHookParser
from json_api_builder import (
    JsonAPIErrorBuilder, JsonAPIResourceDetailBuilder, JsonAPIResourceListBuilder,
    JsonAPIIncludedResourceListBuilder
)


class MockServerBaseViewSet(viewsets.ViewSet):
    def request_contains_include(self, request):
        return 'include' in request.GET.keys()

    def _get_include_ids_from_rel_data(self, rel_data):
        if isinstance(rel_data, list):
            include_ids = [rd['id'] for rd in rel_data]
        else:
            include_ids = [rel_data['id']]
        return include_ids

    def get_include_ids_from_response(self, response, include_type):
        rel_data = response['data']['relationships'][include_type]['data']
        include_ids = self._get_include_ids_from_rel_data(rel_data)
        return set(include_ids)

    def get_include_ids_from_included(self, included, include_type):
        include_ids = []
        include_types = [include_type, singularize(include_type)]
        for include_object in included:
            for include_type in include_types:
                try:
                    rel_data = include_object['relationships'][include_type]['data']
                except:
                    pass
                else:
                    include_ids.extend(self._get_include_ids_from_rel_data(rel_data))
                    break

        return set(include_ids)

    def add_include_objects(self, request, response, length=10, overrides=None):
        include_groups = [group.split('.') for group in request.GET.get('include').split(',')]

        for include_group in include_groups:
            for x, include_type in enumerate(include_group):
                resource_type = pluralize(camelize(include_type, uppercase_first_letter=False))

                if x == 0:
                    include_ids = self.get_include_ids_from_response(response, resource_type)
                else:
                    include_ids = self.get_include_ids_from_included(response['included'], resource_type)


                json_api_builder = JsonAPIIncludedResourceListBuilder(request,
                                                                      include_type,
                                                                      include_ids,
                                                                      self.page_size,
                                                                      length,
                                                                      config=overrides)
                include_objects = json_api_builder.build_include_list()
                if include_objects:
                    response.setdefault("included", []).extend(include_objects)

        return response


class ResourceDetailViewSet(MockServerBaseViewSet):
    allowed_methods = ['GET', 'PATCH', 'DELETE', 'OPTIONS']

    def retrieve(self, request, pk):
        resource_id = pk
        overrides = MockServerHookParser(request, self.attributes).parse_hooks()

        if 'status' in overrides:
            return HttpResponse(status=overrides['status'])

        self.attributes.update(overrides.get('attributes', {}))
        json_api_builder = JsonAPIResourceDetailBuilder(request,
                                                        resource_type=self.resource_type,
                                                        resource_id=resource_id,
                                                        config=overrides)
        response = json_api_builder.build_resource_detail_object()

        if self.request_contains_include(request):
            response = self.add_include_objects(request, response, overrides=overrides)

        return JsonResponse(response, status=200, content_type="application/vnd.api+json")

    def partial_update(self, request, pk):
        resource_id = pk
        overrides = MockServerHookParser(request, self.attributes).parse_hooks()

        if 'status' in overrides:
            return HttpResponse(status=overrides['status'])

        try:
            request_data = json.loads(request.body)
            if 'attributes' in request_data.get('data', {}):
                overrides['attributes'].update(request_data['data']['attributes'])
        except:
            pass

        self.attributes.update(overrides.get('attributes', {}))
        json_api_builder = JsonAPIResourceDetailBuilder(request,
                                                        resource_type=self.resource_type,
                                                        resource_id=resource_id,
                                                        config=overrides)
        response = json_api_builder.build_resource_detail_object()

        return JsonResponse(response, status=200, content_type="application/vnd.api+json")

    def destroy(self, request, pk):
        resource_id = pk
        overrides = MockServerHookParser(request, self.attributes).parse_hooks()

        if 'status' in overrides:
            return HttpResponse(status=overrides['status'])

        return HttpResponse(status=204)


class ResourceListViewSet(MockServerBaseViewSet):
    allowed_methods = ['GET', 'POST', 'OPTIONS']

    def list(self, request):
        overrides = MockServerHookParser(request, self.attributes).parse_hooks()

        if 'status' in overrides:
            return HttpResponse(status=overrides['status'])

        curr_page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', self.page_size))

        filter_configs = self._parse_filters_from_query_parameters(request)
        overrides['filter'] = filter_configs

        length = overrides['length'] if 'length' in overrides else settings.MS_DEFAULT_LIST_LENGTH
        if len(overrides['filter']):
            if 'id' in overrides['filter'].keys():
                length = len(overrides['filter']['id'])
            else:
                length = length/2

        json_api_builder = JsonAPIResourceListBuilder(request,
                                                      self.resource_type,
                                                      page_size,
                                                      length,
                                                      config=overrides,
                                                      curr_page=curr_page)
        response = json_api_builder.build_resource_list_object()

        if self.request_contains_include(request):
            response = self.add_include_objects(request, response, overrides=overrides)

        return JsonResponse(response, status=200, content_type="application/vnd.api+json")

    def create(self, request):
        overrides = MockServerHookParser(request, self.attributes).parse_hooks()

        if 'status' in overrides:
            return HttpResponse(status=overrides['status'])

        try:
            post_data = json.loads(request.body)
            resource_id = 1
            resource_type = post_data['data']['type']
            attributes = post_data['data']['attributes']
            relationships = self._parse_relationship_data(post_data)
            json_api_rules = []
            is_valid_request = True
        except:
            is_valid_request = False

        if 'errors' in overrides:
            json_api_builder = JsonAPIErrorBuilder(request)
            response = json_api_builder.build_error_list_object(overrides['errors'])
            return JsonResponse(response, status=400, content_type="application/vnd.api+json")
        elif not is_valid_request:
            json_api_builder = JsonAPIErrorBuilder(request)
            response = json_api_builder.build_error_list_object(self.attributes)
            return JsonResponse(response, status=400, content_type="application/vnd.api+json")
        else:
            json_api_builder = JsonAPIResourceDetailBuilder(request,
                                                            resource_type=resource_type,
                                                            resource_id=resource_id,
                                                            config=overrides)
            response = json_api_builder.build_resource_detail_object()

            return JsonResponse(response, status=201, content_type="application/vnd.api+json")

    def _parse_filters_from_query_parameters(self, request):
        filter_configs = {}
        for param, values in request.GET.iteritems():
            if param.startswith('filter'):
                try:
                    attribute = re.search(r'\[(.*?)\]', param).group(1)
                    if '__' in attribute:
                        attribute, _ = attribute.split('__')
                except:
                    continue

                try:
                    values = [int(value) for value in values.split(',')]
                except:
                    values = value.split(',')

                filter_configs[attribute] = values

        return filter_configs


    def _parse_relationship_data(self, post_data):
        relationships_definitions = []
        relationships = post_data['data'].get("relationships", {})
        for related_resource_type, relationship_data in relationships.iteritems():
            relationship_data = relationship_data['data']
            if type(relationship_data) == list:
                related_ids = [rd.get('id') for rd in relationship_data]
            else:
                related_ids = relationship_data.get('id')

            relationships_definitions.append((related_resource_type, related_ids))
        return relationships_definitions


class ResourceViewSet(ResourceListViewSet, ResourceDetailViewSet):
    allowed_methods = ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS']
