import hashlib
import traceback
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time

from thasus.persistence.discovered_domains import get_all_domains, update_domains, get_all_test_domains

DAY_IN_MILLIS = 24 * 60 * 60 * 1000
WEEK_IN_MILLIS = 7 * DAY_IN_MILLIS

ignore_domains = [
    'tilthalliance.org'
]


def update_website_freshness(current_time_epoch):
    """Function to check whether a website is 'fresh', and if it is not, update it.

    Freshness is determined by whether a website has been updated in a certain amount of time.
    Additionally, a website can still be fresh even if it is old. Page content is taken as a string and hashed.
    If the hash matches, the website is still fresh, but its timestamp gets updated.

    :param current_time_epoch: current time as an int
    :return: None
    """

    # all_domains = get_all_domains()
    all_domains = get_all_test_domains(current_time_epoch)
    print(f"Found domains - {len(all_domains)}")

    updated_domains = list()  # list of domains that have been updated. currently has no use
    for domain in all_domains:
        # do not update domain if it is fresh
        if is_website_content_fresh(domain, current_time_epoch):
            continue
        # do not update blacklisted domains
        if domain['domain'] in ignore_domains:
            continue

        start = time.time()  # timestamp marker for when this domain started its scan
        page_content = get_page_content(domain).encode('utf-8')  # String: obtain the page content
        content_extraction_time = time.time()  # timestamp marker for when the content finished extracting

        # todo think about taking the hash of the important part of the page (specific spans or divs)
        page_content_hash = hashlib.md5(page_content).hexdigest()  # calculate the hash based on the page content
        hash_time = time.time()  # timestamp marker for when the hash finishes calculating

        # if the domain does not have a hash or the hash does not match:
        if 'website_hash' not in domain or domain['website_hash'] != page_content_hash:
            domain['website_hash'] = page_content_hash  # replace hash for the domain
            domain['content_status'] = 'extract'  # update content status
        domain['scanned_at'] = current_time_epoch  # update timestamp for domain

        # print how long this operation took
        print(f"{domain['domain_name']} extracted in "
              f"{content_extraction_time - start} "
              f"and hashed in {hash_time - content_extraction_time}"
              )
        updated_domains.append(domain)  # attach updated domain to a list

    # execute
    # update_domains(updated_domains)


def is_website_content_fresh(domain, current_time_epoch):
    """Determines whether content is "fresh enough".

    A domain is considered not fresh if it was never scanned or was scanned at least one full day ago.

    :param domain: domain to determine freshness of
    :param current_time_epoch: current time as an int
    :return: Boolean
    """

    if 'scanned_at' not in domain:
        return False

    freshness_threshold = current_time_epoch - DAY_IN_MILLIS

    if domain['scanned_at'] <= freshness_threshold:
        return False

    return True


def get_page_content(domain):
    """Gets page content from a domain. Uses BeautifulSoup to parse HTML.

    :param domain: domain to get the content from. should contain url
    :return: massive String representing page text
    """

    # attempt to request data from the domain and parse it into a string
    try:
        hdr = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.0.0 Safari/537.36',
        }
        print(f"Extracting domain {domain['domain']}")
        req = Request(domain['url'], headers=hdr)
        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
        return soup.getText()

    # if it fails, print that it failed as well as the error and traceback
    except Exception as e:
        print(f"Unable to get camp data for {domain['url']}")
        print(e)
        print(traceback.format_exc())
