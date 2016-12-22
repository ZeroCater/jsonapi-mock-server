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


class TestFaker(MockServerBaseTestCase):
    faker_qs = "?faker=1"

    def do_test(self):
        response = self.client.get(self.path + self.faker_qs)
        self.assertEqual(response.status_code, 200)


class TestJsonResponses(MockServerBaseTestCase):
    maxDiff = None
    master_origin = settings.MASTER_ORIGIN
    master_staff_email = settings.MASTER_STAFF_EMAIL
    master_staff_psswd = settings.MASTER_STAFF_PASSWORD

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

    def get_responses(self, path):
        try:
            mock_response = self.client.get(path)
            mock_json = json.loads(mock_response.content.decode())
        except JSONDecodeError, e:
            self.fail("Unable to parse JSON response from mock server response:\n{}, {}\n {}"
                      .format(mock_url, mock_response, mock_response.text))

        try:
            master_url = "{}{}".format(self.master_origin, path)
            master_headers = {"Authorization": "Token %s" % self.master_token}
            master_response = requests.get(master_url, headers=master_headers)
            master_json = master_response.json()
        except JSONDecodeError, e:
            self.fail("Unable to parse JSON response from master server response:\n{}, {}\n {}"
                      .format(master_url, master_response, master_response.text))

        return master_url, master_json, path, mock_json

    def assertJsonStructureEqual(self, master_url, master_json, mock_url, mock_json):
        master_json_simple = simplify_json(master_json)
        mock_json_simple = simplify_json(mock_json)
        d = diff(master_json_simple, mock_json_simple)
        error_msg = [
            "master url:\n{}".format(master_url),
            "master response:\n{}\n".format(pprint.pformat(master_json_simple)),
            "mock url:\n{}".format(mock_url),
            "mock response:\n{}\n".format(pprint.pformat(mock_json_simple)),
            "diff:\n{}".format(pprint.pformat(d))
        ]
        self.assertEqual(d, {}, '\n'.join(error_msg))

    def do_test(self):
        master_url, master_json, mock_url, mock_json = self.get_responses(self.path)
        self.assertJsonStructureEqual(master_url, master_json, mock_url, mock_json)


class DatabaselessTestRunner(DiscoverRunner):
    """A test suite runner that does not set up and tear down a database."""

    def setup_databases(self):
        """Overrides DjangoTestSuiteRunner"""
        pass

    def teardown_databases(self, *args):
        """Overrides DjangoTestSuiteRunner"""
        pass
