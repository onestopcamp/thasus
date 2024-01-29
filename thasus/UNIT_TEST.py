"""Program containing unit tests for the following programs:
- website_scanner.py

"""

import unittest
import pytest
from parameterized import parameterized
from thasus.website_scanner import is_website_content_fresh, check_hash
from lambda_function import get_now

DAY_IN_MILLIS = 24 * 60 * 60 * 1000


# @pytest.fixture(scope="class")
class TestFreshness(unittest.TestCase):

    @parameterized.expand([
        (get_now(), -1),  # older than time epoch; not fresh
        (get_now(), 0),  # same age as time epoch; not fresh
        (get_now(), 1)  # younger than time epoch; fresh
    ])
    def test_timestamp(self, current_time_epoch, offset):
        """Tests the function is_website_content_fresh.

        False means not fresh, True means fresh. Since the current freshness modifier is one day, the test domain is
        set to have a scanned time of exactly one day old, plus or minus an offset of one millisecond.

        The domain is also given a new timestamp.
        """

        # declare test domain
        domain = {
            'scanned_at': current_time_epoch - DAY_IN_MILLIS + offset
        }

        # actual test cases
        if offset > 0:
            # if the offset is above 0, that means that the time is higher, which is closer to current time
            assert is_website_content_fresh(domain, current_time_epoch)
        else:
            # Fresh / True
            assert not is_website_content_fresh(domain, current_time_epoch)

        # make sure the 'scanned_at' field is updated
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

        # if the hash needed updating, make sure content_status reflects that
        if hash_old != hash_new:
            assert domain['content_status'] == 'extract'
        else:
            assert domain['content_status'] != 'extract'
