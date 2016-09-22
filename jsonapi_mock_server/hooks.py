class BaseHookParser(object):
    def __init__(self, request):
        self.request = request

    def cast(self, value):
        try:
            return int(value)
        except:
            return value

    def parse_hooks(self):
        fake = self._extract_fake()
        length = self._extract_length()
        status = self._extract_status()
        errors = self._extract_errors()
        attributes = self._extract_attributes()

        overrides = {}
        if fake is not None:
            overrides.update({"fake": fake})
        if length or length == 0:
            overrides.update({"length": length})
        if status:
            overrides.update({"status": status})
        if errors:
            overrides.update({"errors": errors})
        if attributes:
            overrides.update({"attributes": attributes})

        return overrides

    def _extract_errors(self):
        raise NotImplementedError

    def _extract_attributes(self):
        raise NotImplementedError

    def _extract_length(self):
        raise NotImplementedError

    def _extract_status(self):
        raise NotImplementedError

    def _extract_fake(self):
        raise NotImplementedError

    def parse_bool(self, value):
        if value is None:
            return None
        elif value in ('false', 'False', '0', '[]'):
            return False
        else:
            return bool(value)


class QueryStringHookParser(BaseHookParser):
    """
    Example of valid query string:

      /caterers/1?length=20&name=abc&numberOfDrivers=10&errors=name,description&fake=1

    """
    def __init__(self, request, attributes):
        super(QueryStringHookParser, self).__init__(request)
        self.attributes = attributes

        self.overrides = {}
        for param, value in self.request.GET.iteritems():
            self.overrides[param] = self.cast(value)

    def _extract_errors(self):
        if 'errors' in self.overrides:
            return self.overrides['errors'].split(',')

    def _extract_attributes(self):
        return {attr: val for attr, val in self.overrides.iteritems() if attr in self.attributes.keys()}

    def _extract_length(self):
        return self.overrides.get('length')

    def _extract_status(self):
        return self.overrides.get('status')

    def _extract_fake(self):
        return self.parse_bool(self.overrides.get('fake'))


class HeadersHookParser(BaseHookParser):
    """
    Example of valid headers:

      HOST: local.zerocater.com
      ms-length: 20
      ms-attributes: name=abc;numberOfDrivers=10
      ms-errors: name;description
      ms-fake: 1

    """
    def __init__(self, request):
        super(HeadersHookParser, self).__init__(request)

        self.overrides = {}
        for header, value in self.request.META.iteritems():
            if header.lower().startswith('http_ms_'):
                self.overrides[header[8:].lower()] = self.cast(value)

    def _extract_errors(self):
        if 'errors' in self.overrides:
            return self.overrides['errors'].split(';')

    def _extract_attributes(self):
        if 'attributes' not in self.overrides:
            return None

        attributes = self.overrides['attributes'].split(';')
        attribute_overrides = dict([attribute.split('=') for attribute in attributes])
        for att, value in attribute_overrides.iteritems():
            attribute_overrides[att] = self.cast(value)
        return attribute_overrides

    def _extract_length(self):
        return self.overrides.get('length')

    def _extract_status(self):
        return self.overrides.get('status')

    def _extract_fake(self):
        return self.parse_bool(self.overrides.get('fake'))


class MockServerHookParser(object):
    def __init__(self, request, attributes):
        self.headers_hook_parser = HeadersHookParser(request)
        self.qs_hook_parser = QueryStringHookParser(request, attributes)

    def parse_hooks(self):
        overrides = {}
        overrides.update(self.headers_hook_parser.parse_hooks())
        overrides.update(self.qs_hook_parser.parse_hooks())
        return overrides
