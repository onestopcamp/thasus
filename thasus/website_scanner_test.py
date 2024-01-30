"""Program containing unit tests for website_scanner.py

"""

import unittest
#import pytest
from parameterized import parameterized
from thasus.website_scanner import is_website_content_fresh, check_hash, get_page_content
#from lambda_function import get_now

DAY_IN_MILLIS = 24 * 60 * 60 * 1000
current_time_epoch = 1706574375  # example time


# @pytest.fixture(scope="class")
class TestFreshness(unittest.TestCase):

    @parameterized.expand([
        (current_time_epoch - DAY_IN_MILLIS - 1, False),  # older than time epoch; not fresh
        (current_time_epoch - DAY_IN_MILLIS, False),  # same age as time epoch; not fresh
        (current_time_epoch - DAY_IN_MILLIS + 1, True)  # younger than time epoch; fresh
    ])
    def test_timestamp(self, test_time_epoch, expected_result):
        """Tests the function is_website_content_fresh.

        False means not fresh, True means fresh. Since the current freshness modifier is one day, the test domain is
        set to have a scanned time of exactly one day old, plus or minus an 'offset' of one millisecond.

        The domain is also given a new timestamp.
        """

        # declare test domain
        domain = {
            'scanned_at': test_time_epoch
        }

        # make sure expected result matches the actual result of the function
        self.assertEqual(expected_result, is_website_content_fresh(domain, current_time_epoch))

        # make sure the 'scanned_at' field is updated to the "current" time
        assert domain['scanned_at'] == current_time_epoch

    @parameterized.expand([
        ("e062a63e86748efb4fcefbdb278e7d8c", "e062a63e86748efb4fcefbdb278e7d8c"),  # two identical garbage MD5 hashes
        ("e062a63e86748efb4fcefbdb278e7d8c", "6117100570fd43294a78af8611e36697"),  # two different garbage MD5 hashes
        (None, "6117100570fd43294a78af8611e36697")  # no hash and a garbage MD5 hash
    ])
    def test_hash_compare(self, hash_old, hash_new):
        """Tests the function check_hash.

        The function to be tested is passed in a domain with either an existing hash or no hash at all.
        In all cases, the domain should contain hash_new if checked. However, the domain's content-status
        should only be set to 'extract' if the hash needed to be changed.

        """

        # declare test domain
        domain = {
            'website_hash': hash_old,
            'content_status': 'ready'  # garbage placeholder value
        }

        # run check_hash and make sure the hash is current
        check_hash(domain, hash_new)
        assert domain['website_hash'] == hash_new

        # if the domain's hash did not match, meaning the domain needs updating, make sure content_status reflects that
        if hash_old != hash_new:
            assert domain['content_status'] == 'extract'
        else:
            assert domain['content_status'] != 'extract'

    @parameterized.expand([
        ('https://www.illuminationlearningstudio.com/summer-camps-2024/', True),  # may not work in the future
        ('https://dsgbkds.dfjgkd.sdkgfjh', False)  # expected to fail, obviously
    ])
    def test_get_page_content(self, url, expected_result):
        """Tests the function get_page_content.

        The function is passed a domain which contains a url field and a domain name. It should be able to be properly
        scanned, but if not, it will print an error and return it as part of a tuple.

        """

        # declare test domain
        domain = {
            'domain': str(expected_result),  # garbage value
            'url': url
        }

        actual_result = get_page_content(domain)
        # successful scans return page content and have None as their error message
        if expected_result:
            self.assertIsNone(actual_result[1])

        # failed scans return an error message
        else:
            self.assertIsNotNone(actual_result[1])
