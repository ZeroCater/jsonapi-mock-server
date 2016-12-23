import json
import os
import pprint
import requests
from simplejson.decoder import JSONDecodeError
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client
from django.test.runner import DiscoverRunner
from jsondiff import diff
import inflection

from jsonapi_mock_server.base_views import ResourceDetailViewSet, ResourceListViewSet


def simplify_json(obj):
    for key, value in obj.iteritems():
        is_resource_list = (key == 'data' and type(value) is list and len(value) > 1)

        if type(value) is dict:
            simplify_json(value)
        elif is_resource_list:
            # normalize master/mock resource list lengths to 1 resource object for comparison
            obj[key] = value[0:1]
            simplify_json(obj[key][0])
        else:
            obj[key] = ''

    return obj


class MockServerBaseTestCase(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.client = Client()

    def get_json(self, response):
        return json.loads(response.content.decode())


class TestJsonResponses(MockServerBaseTestCase):
    maxDiff = None
    master_origin = settings.MASTER_ORIGIN
    master_staff_email = settings.MASTER_STAFF_EMAIL
    master_staff_psswd = settings.MASTER_STAFF_PSSWD

    @classmethod
    def get_auth_token(cls):
        login_post_data = {
            "data": {
                "type": "Login",
                "attributes": {
                    "email": cls.master_staff_email,
                    "password": cls.master_staff_psswd
                }
            }
        }

        headers = {"Content-Type": "application/json"}
        master_url = "{}/login".format(cls.master_origin)
        master_response = requests.post(master_url, data=json.dumps(login_post_data), headers=headers)
        if master_response.status_code != requests.codes.ok:
            raise Exception("Login to {} returned {} using data:\n{}".format(
                master_url, master_response.status_code, login_post_data))
        master_json = master_response.json()
        return master_json['data']['token']

    @classmethod
    def setUpClass(cls):
        super(TestJsonResponses, cls).setUpClass()

        try:
            cls.master_token = cls.get_auth_token()
        except Exception, e:
            raise Exception("Unable to obtain auth token: {}".format(e))

    def assertJsonStructureEqual(self, master_json, mock_json):
        master_json_simple = simplify_json(master_json)
        mock_json_simple = simplify_json(mock_json)
        d = diff(master_json_simple, mock_json_simple)
        error_msg = [
            "master url:\n{}".format(self.master_url),
            "master response:\n{}\n".format(pprint.pformat(master_json_simple)),
            "mock url:\n{}".format(self.path),
            "mock response:\n{}\n".format(pprint.pformat(mock_json_simple)),
            "diff:\n{}".format(pprint.pformat(d))
        ]
        self.assertEqual(d, {}, '\n'.join(error_msg))

    def get_mock_response(self, url):
        try:
            mock_response = self.client.get(url)
            mock_json = json.loads(mock_response.content.decode())
        except JSONDecodeError, e:
            self.fail("Unable to parse JSON response from mock server response:\n{}, {}\n {}"
                      .format(url, mock_response, mock_response.text))
        return mock_json

    def get_master_response(self, url):
        try:
            master_headers = {"Authorization": "Token %s" % self.master_token}
            master_response = requests.get(url, headers=master_headers)
            master_json = master_response.json()
        except JSONDecodeError, e:
            self.fail("Unable to parse JSON response from master server response:\n{}, {}\n {}"
                      .format(url, master_response, master_response.text))
        return master_response, master_json

    def get_master_resource_id(self):
        master_list_url = "{}{}".format(self.master_origin, self.get_list_path())
        master_headers = {"Authorization": "Token %s" % self.master_token}
        master_response = requests.get(master_list_url, headers=master_headers)
        master_json = master_response.json()
        resource_id = master_json['data'][0]['id']
        return resource_id

    def get_detail_path(self, resource_id=1):
        return reverse('{}-detail'.format(self.router_base_name), args=(resource_id,))

    def get_list_path(self):
        return reverse('{}-list'.format(self.router_base_name))

    @property
    def router_base_name(self):
        return inflection.dasherize(inflection.underscore(self.viewset.resource_type)).lower()

    def _test_view(self):
        mock_json = self.get_mock_response(self.path)
        self.master_url = "{}{}".format(self.master_origin, self.path)
        master_response, master_json = self.get_master_response(self.master_url)
        self.assertJsonStructureEqual(master_json, mock_json)

    def test_detail_view(self, path=None):
        if not issubclass(self.viewset, ResourceDetailViewSet):
            self.skipTest("No detail view defined for for {}".format(self.viewset.resource_type))

        self.path = path if path else self.get_detail_path()
        self.master_url = "{}{}".format(self.master_origin, self.path)

        mock_json = self.get_mock_response(self.path)
        master_response, master_json = self.get_master_response(self.master_url)

        if master_response.status_code == 404:
            try:
                master_resource_id = self.get_master_resource_id()
                self.path = self.get_detail_path(resource_id=master_resource_id)
                self.master_url = "{}{}".format(self.master_origin, self.path)
                master_response, master_json = self.get_master_response(self.master_url)
            except:
                pass

        self.assertJsonStructureEqual(master_json, mock_json)

    def test_list_view(self, path=None):
        if not issubclass(self.viewset, ResourceListViewSet):
            self.skipTest("No list view defined for for {}".format(self.viewset.resource_type))

        self.path = path if path else self.get_list_path()
        self.master_url = "{}{}".format(self.master_origin, self.path)

        mock_json = self.get_mock_response(self.path)
        master_response, master_json = self.get_master_response(self.master_url)
        self.assertJsonStructureEqual(master_json, mock_json)

    def test_faker(self, path=None):
        faker_qs = "?faker=1"
        self.path = path if path else self.get_detail_path()
        response = self.client.get("{}{}".format(self.path, faker_qs))
        self.assertEqual(response.status_code, 200)


class DatabaselessTestRunner(DiscoverRunner):
    """A test suite runner that does not set up and tear down a database."""

    def setup_databases(self):
        """Overrides DjangoTestSuiteRunner"""
        pass

    def teardown_databases(self, *args):
        """Overrides DjangoTestSuiteRunner"""
        pass
