import json
import re

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from rest_framework import viewsets

from hooks import MockServerHookParser
from json_api_builder import JsonAPIErrorBuilder, JsonAPIResourceDetailBuilder, JsonAPIResourceListBuilder


class MockServerBaseViewSet(viewsets.ViewSet):
    def request_contains_include(self, request):
        return 'include' in request.GET.keys()

    def add_include_object(self, request, response, length=10, overrides=None):
        include_resource_types = re.split(r'[,\.]', request.GET.get('include'))

        for include_resource_type in include_resource_types:
            json_api_builder = JsonAPIResourceListBuilder(request,
                                                          include_resource_type,
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
            response = self.add_include_object(request, response, overrides=overrides)

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
            response = self.add_include_object(request, response, overrides=overrides)

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
