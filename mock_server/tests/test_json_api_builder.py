import json

from django.core.urlresolvers import reverse

from mock_server.base_tests import MockServerBaseTestCase


class JsonApiBuilderTests(MockServerBaseTestCase):
    def test_resource_list_next_link__empty_list(self):
        length = 0
        path = reverse("caterer-list") + "?length={}".format(length)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['links']['next'], None)

    def test_resource_list_next_link__only_one_page(self):
        length = 10
        page_size = 10
        path = reverse("caterer-list") + "?length={}&page_size={}".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['links']['next'], None)

    def test_resource_list_next_link__has_next_page(self):
        length = 11
        page_size = 10
        path = reverse("caterer-list") + "?length={}&page_size={}".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        expected_next_link = "http://None/caterers?page=2"
        self.assertEqual(response_json['links']['next'], expected_next_link)

    def test_resource_list_prev_link__empty_list(self):
        length = 0
        path = reverse("caterer-list") + "?length={}".format(length)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['links']['prev'], None)

    def test_resource_list_prev_link__no_prev_page(self):
        length = 11
        page_size = 10
        curr_page = 1
        qs = "?length={}&page_size={}&page={}".format(length, page_size, curr_page)
        path = reverse("caterer-list") + qs
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['links']['prev'], None)

    def test_resource_list_prev_link__has_prev_page(self):
        length = 11
        page_size = 10
        curr_page = 2
        qs = "?length={}&page_size={}&page={}".format(length, page_size, curr_page)
        path = reverse("caterer-list") + qs
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['links']['prev'], "http://None/caterers?page=1")

    def test_resource_list_filter_id_in(self):
        filter_ids = ['4', '5', '6']
        qs = "?filter[id__in]={}".format(','.join(filter_ids))
        path = reverse("caterer-list") + qs
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['meta']['pagination']['count'], len(filter_ids))
        self.assertEqual(response_json['data'][0]['id'], filter_ids[0])
        self.assertEqual(response_json['data'][1]['id'], filter_ids[1])
        self.assertEqual(response_json['data'][2]['id'], filter_ids[2])

    def test_resource_list_filter_not_by_id(self):
        qs = "?filter[category]=1"
        path = reverse("caterer-list") + qs
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['meta']['pagination']['count'], 5)

    def test_page_size__page_count(self):
        length = 10
        page_size = 5
        expected_pages = length/page_size
        path = reverse("caterer-list") + "?length={}&page_size={}".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(response_json['meta']['pagination']['count'], length)
        self.assertEqual(response_json['meta']['pagination']['pages'], expected_pages)

    def test_page_size__first_page(self):
        length = 12
        page_size = 10
        expected_first_page_size = 10
        path = reverse("caterer-list") + "?length={}&page_size={}".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(len(response_json['data']), expected_first_page_size)
        self.assertEqual(int(response_json['data'][0]['id']), 1)
        self.assertEqual(int(response_json['data'][-1]['id']), 10)

    def test_page_size__last_page(self):
        length = 12
        page_size = 10
        expected_last_page_size = 2
        path = reverse("caterer-list") + "?length={}&page_size={}&page=2".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(len(response_json['data']), expected_last_page_size)
        self.assertEqual(int(response_json['data'][0]['id']), 11)
        self.assertEqual(int(response_json['data'][-1]['id']), 12)

    def test_page_size__only_page(self):
        length = 3
        page_size = 10
        path = reverse("caterer-list") + "?length={}&page_size={}".format(length, page_size)
        response = self.client.get(path)
        response_json = self.get_json(response)
        self.assertEqual(len(response_json['data']), length)
        self.assertEqual(int(response_json['data'][0]['id']), 1)
        self.assertEqual(int(response_json['data'][-1]['id']), 3)

    def test_m2m_relationships_links(self):
        path = reverse("caterer-detail", args=(1,))
        response = self.client.get(path)
        response_json = self.get_json(response)

        expected_self_link = "http://None/caterers/1/relationships/delivery_fees"
        expected_rel_link = "http://None/caterers/1/delivery_fees"
        actual_self_link = response_json['data']['relationships']['deliveryFees']['links']['self']
        actual_rel_link = response_json['data']['relationships']['deliveryFees']['links']['related']

        self.assertEqual(expected_self_link, actual_self_link)
        self.assertEqual(expected_rel_link, actual_rel_link)

    def test_m2one_relationships_links(self):
        path = reverse("dish-detail", args=(1,))
        response = self.client.get(path)
        response_json = self.get_json(response)

        expected_self_link = "http://None/dishes/1/relationships/caterers"
        expected_rel_link = "http://None/caterers/22"
        actual_self_link = response_json['data']['relationships']['caterer']['links']['self']
        actual_rel_link = response_json['data']['relationships']['caterer']['links']['related']

        self.assertEqual(expected_self_link, actual_self_link)
        self.assertEqual(expected_rel_link, actual_rel_link)
