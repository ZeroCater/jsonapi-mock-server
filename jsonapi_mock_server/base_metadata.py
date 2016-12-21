from collections import OrderedDict

from rest_framework.metadata import SimpleMetadata

class MockServerMetadata(SimpleMetadata):
    def determine_metadata(self, request, view):
        metadata = OrderedDict()
        metadata['name'] = view.get_view_name()
        metadata['description'] = view.get_view_description()
        metadata['renders'] = [renderer.media_type for renderer in view.renderer_classes]
        metadata['parses'] = [parser.media_type for parser in view.parser_classes]
        metadata['allowed_methods'] = view.allowed_methods
        metadata['actions'] = self.determine_actions(request, view)
        return {'data': metadata}

    def determine_actions(self, request, view):
        actions = {}
        action_data = view.get_action_metadata()
        actions['POST'] = action_data
        actions['PUT'] = action_data

        return actions
