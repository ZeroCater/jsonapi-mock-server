from django.core.urlresolvers import reverse
from django.test import RequestFactory

from mock_server.base_tests import MockServerBaseTestCase
from mock_server.hooks import BaseHookParser, HeadersHookParser, QueryStringHookParser, MockServerHookParser
from resources.caterer import CatererViewSet, CatererResource


class BaseHookParserTests(MockServerBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseHookParserTests, cls).setUpClass()
        cls.base_hook_parser = BaseHookParser(None)

    def test_parse_bool__1(self):
        parsed = self.base_hook_parser.parse_bool(1)
        self.assertEqual(parsed, True)

    def test_parse_bool__0_int(self):
        parsed = self.base_hook_parser.parse_bool(0)
        self.assertEqual(parsed, False)

    def test_parse_bool__0_string(self):
        parsed = self.base_hook_parser.parse_bool('0')
        self.assertEqual(parsed, False)

    def test_parse_bool__false(self):
        parsed = self.base_hook_parser.parse_bool('false')
        self.assertEqual(parsed, False)

    def test_parse_bool__False(self):
        parsed = self.base_hook_parser.parse_bool('False')
        self.assertEqual(parsed, False)

    def test_parse_bool__None(self):
        parsed = self.base_hook_parser.parse_bool(None)
        self.assertEqual(parsed, None)


class QueryStringHookParserTests(MockServerBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(QueryStringHookParserTests, cls).setUpClass()
        cls.factory = RequestFactory()

    def setUp(self):
        self.attributes = CatererResource().get_attributes()

    def test_parse_hooks__passed_fake_qs_param_of_1(self):
        expected_overrides = {"fake": True}
        path = "{}?fake={}".format(reverse("caterer-detail", args=(1,)), 1)
        request = self.factory.get(path)
        qs_hook_parser = QueryStringHookParser(request, self.attributes)
        overrides = qs_hook_parser.parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__passed_fake_qs_param_of_true(self):
        expected_overrides = {"fake": True}
        path = "{}?fake=true".format(reverse("caterer-detail", args=(1,)))
        request = self.factory.get(path)
        qs_hook_parser = QueryStringHookParser(request, self.attributes)
        overrides = qs_hook_parser.parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__passed_fake_qs_param_of_0(self):
        expected_overrides = {"fake": False}
        path = "{}?fake={}".format(reverse("caterer-detail", args=(1,)), 0)
        request = self.factory.get(path)
        qs_hook_parser = QueryStringHookParser(request, self.attributes)
        overrides = qs_hook_parser.parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hook__passed_fake_qs_param_of_false(self):
        expected_overrides = {"fake": False}
        path = "{}?fake=false".format(reverse("caterer-detail", args=(1,)))
        request = self.factory.get(path)
        qs_hook_parser = QueryStringHookParser(request, self.attributes)
        overrides = qs_hook_parser.parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__no_fake_qs_param(self):
        expected_overrides = {}
        path = reverse("caterer-detail", args=(1,))
        request = self.factory.get(path)
        qs_hook_parser = QueryStringHookParser(request, self.attributes)
        overrides = qs_hook_parser.parse_hooks()
        self.assertEqual(overrides, expected_overrides)


class HeadersHookParserTests(MockServerBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(HeadersHookParserTests, cls).setUpClass()
        cls.factory = RequestFactory()

    def test_parse_hooks__passed_fake_qs_param_of_1(self):
        expected_overrides = {"fake": True}
        path = reverse("caterer-detail", args=(1,))
        headers = {"HTTP_MS_FAKE": 1}
        request = self.factory.get(path, **headers)
        overrides = HeadersHookParser(request).parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__passed_fake_qs_param_of_true(self):
        expected_overrides = {"fake": True}
        path = reverse("caterer-detail", args=(1,))
        headers = {"HTTP_MS_FAKE": True}
        request = self.factory.get(path, **headers)
        overrides = HeadersHookParser(request).parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__passed_fake_qs_param_of_0(self):
        expected_overrides = {"fake": False}
        path = reverse("caterer-detail", args=(1,))
        headers = {"HTTP_MS_FAKE": 0}
        request = self.factory.get(path, **headers)
        overrides = HeadersHookParser(request).parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hook__passed_fake_qs_param_of_false(self):
        expected_overrides = {"fake": False}
        path = reverse("caterer-detail", args=(1,))
        headers = {"HTTP_MS_FAKE": False}
        request = self.factory.get(path, **headers)
        overrides = HeadersHookParser(request).parse_hooks()
        self.assertEqual(overrides, expected_overrides)

    def test_parse_hooks__no_fake_qs_param(self):
        expected_overrides = {}
        path = reverse("caterer-detail", args=(1,))
        request = self.factory.get(path)
        overrides = HeadersHookParser(request).parse_hooks()
        self.assertEqual(overrides, expected_overrides)


class MockServerHookParserTests(MockServerBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(MockServerHookParserTests, cls).setUpClass()
        cls.factory = RequestFactory()

    def test_parse_query_string__no_params(self):
        path = reverse("caterer-detail", args=(1,))
        request = self.factory.get(path)
        attributes = CatererViewSet().attributes
        parsed = MockServerHookParser(request, attributes).parse_hooks()
        self.assertEqual(parsed, {})

    def test_parse_query_string__with_params(self):
        expected = {
            "length": 20,
            "status": 400,
            "fake": False,
            "errors": ["name", "description"],
            "attributes": {
                "name": "abc",
                "numberOfDrivers": 10
            }
        }

        query_string = "length=20&name=abc&numberOfDrivers=10&errors=name,description&status=400&fake=0"
        path = reverse("caterer-detail", args=(1,)) + "?" + query_string
        request = self.factory.get(path)
        attributes = CatererViewSet().attributes
        parsed = MockServerHookParser(request, attributes).parse_hooks()
        self.assertEqual(parsed, expected)

    def test_parse_headers__no_headers(self):
        path = reverse("caterer-detail", args=(1,))
        request = self.factory.get(path)
        attributes = CatererViewSet().attributes
        parsed = MockServerHookParser(request, attributes).parse_hooks()
        self.assertEqual(parsed, {})

    def test_parse_headers__with_headers(self):
        expected = {
            "length": 20,
            "status": 400,
            "fake": False,
            "errors": ["name", "description"],
            "attributes": {
                "name": "abc",
                "numberOfDrivers": 10
            }
        }

        headers = {
            "HTTP_MS_LENGTH": 20,
            "HTTP_MS_STATUS": 400,
            "HTTP_MS_FAKE": 0,
            "HTTP_MS_ERRORS": "name;description",
            "HTTP_MS_ATTRIBUTES": "name=abc;numberOfDrivers=10",
        }
        path = reverse("caterer-detail", args=(1,))
        request = self.factory.get(path, **headers)
        attributes = CatererViewSet().attributes
        parsed = MockServerHookParser(request, attributes).parse_hooks()
        self.assertEqual(parsed, expected)

    def test_override_status(self):
        status_code = 400
        detail_path = "{}?status={}".format(reverse("caterer-detail", args=(1,)), status_code)
        list_path = "{}?status={}".format(reverse("caterer-list"), status_code)

        response = self.client.get(detail_path)
        self.assertEqual(response.status_code, status_code)
        response = self.client.patch(detail_path, {})
        self.assertEqual(response.status_code, status_code)
        response = self.client.delete(detail_path)
        self.assertEqual(response.status_code, status_code)

        response = self.client.get(list_path)
        self.assertEqual(response.status_code, status_code)
        response = self.client.post(list_path, {})
        self.assertEqual(response.status_code, status_code)

    def test_override_length(self):
        length = 20
        list_path = "{}?length={}".format(reverse("caterer-list"), length)

        response = self.client.get(list_path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['meta']['pagination']['count'], length)

    def test_override_errors(self):
        errors = "name,description"
        list_path = "{}?errors={}".format(reverse("caterer-list"), errors)

        response = self.client.post(list_path)
        response_json = self.get_json(response)
        self.assertEqual(len(response_json['errors']), len(errors.split(',')))

    def test_override_attributes__get(self):
        attributes = {
            "name": "abc",
            "description": "foobar"
        }
        attributes_string = "&".join("{}={}".format(k,v) for k,v in attributes.iteritems())
        detail_path = "{}?{}".format(
            reverse("caterer-detail", args=(1,)),
            attributes_string)

        response = self.client.get(detail_path)
        response_json = self.get_json(response)
        for k,v in attributes.iteritems():
            self.assertEqual(response_json['data']['attributes'][k], v)
