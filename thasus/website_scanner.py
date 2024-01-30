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

    updated_domains = list()  # list of domains that have been updated.
    failed_domains = list()  # list of domains that failed to be updated.

    for domain in all_domains:
        # do not update domain if it is fresh
        if is_website_content_fresh(domain, current_time_epoch):
            continue
        # do not update blacklisted domains
        if domain['domain'] in ignore_domains:
            continue

        start = time.time()  # timestamp marker for when this domain started its scan
        page_result = get_page_content(domain)  # tuple containing page content and the result of the function

        # failure case.
        if page_result[1] is not None:
            failed_domains.append((domain, page_result[1]))  # attach failed domain and exception text to the list
            continue
        page_content = page_result[0].encode('utf-8')  # String: obtain the page content
        content_extraction_time = time.time()  # timestamp marker for when the content finished extracting

        """ perhaps look into if there is a better way to do this; may be too complex or out of this program's scope.
            the upside is that a double-length md5 hash cannot possibly fail, and the super rare possibility of a hash
            collision is so small that it doesn't really affect the purpose of the hash.
            however, due to the volatile nature of websites, this may cause a large amount of false positives.
            depending on how expensive the scraper is, this may or may not be a big deal.
        """
        page_content_hash = hashlib.md5(page_content).hexdigest()  # calculate the hash based on the page content
        hash_time = time.time()  # timestamp marker for when the hash finishes calculating
        check_hash(domain, page_content_hash)  # updates the hash and content status of a domain if necessary

        # print how long this operation took
        print(f"{domain['domain_name']} extracted in "
              f"{content_extraction_time - start} "
              f"and hashed in {hash_time - content_extraction_time}"
              )
        updated_domains.append(domain)  # attach updated domain to the list

    # NOTE: S3 bucket will be named osc-scraper-thasus

    # failed_domains
    # update_domains(updated_domains)


def is_website_content_fresh(domain, current_time_epoch):
    """Determines whether content is "fresh enough".

    A domain is considered not fresh if it was never scanned or was scanned at least one full day ago.
    Differences SMALLER than DAY_IN_MILLIS indicate freshness, since the offset is in the past. This means closer
    values are newer.
    This function also updates the domain's 'scanned_at' field.

    :param domain: domain to determine freshness of
    :param current_time_epoch: current time as an int
    :return: Boolean representing False for not fresh and True for fresh.
    """

    if 'scanned_at' not in domain:
        domain['scanned_at'] = current_time_epoch  # update timestamp for domain
        return False

    freshness_threshold = current_time_epoch - DAY_IN_MILLIS  # if it's more than a day old, it is not fresh

    # if exactly a day old or more, it is not fresh
    if domain['scanned_at'] <= freshness_threshold:
        domain['scanned_at'] = current_time_epoch  # update timestamp for domain
        return False

    domain['scanned_at'] = current_time_epoch  # update timestamp for domain
    return True


def get_page_content(domain):
    """Gets page content from a domain. Uses BeautifulSoup to parse HTML.

    :param domain: domain to get the content from. should contain url
    :return: a tuple containing: (massive String representing page text, error message)
    """

    # attempt to request data from the domain and parse it into a string
    try:
        hdr = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.0.0 Safari/537.36',  # Spoofs browser user-agents
        }
        print(f"Extracting domain {domain['domain']}")
        req = Request(domain['url'], headers=hdr)  # Request object. Used in the following line.
        page = urlopen(req)  # May raise URLError. Returns an object containing a redirected url among other things.
        soup = BeautifulSoup(page, 'html.parser')  # May raise HTMLParseError.
        # Note: Changing the parser requires rewriting scraping code, as the resulting text would be different.
        return soup.getText(), None

    # if it fails, print that it failed as well as the error and traceback
    except Exception as e:
        print(f"Unable to get camp data for {domain['url']}")
        print(e)
        print(traceback.format_exc())
        return None, e


def check_hash(domain, page_content_hash):
    """Checks if a domain's hash and content status needs updating, and updates it if so.

    If the hash needed to be inserted or updated, content_status is set to 'extract'.

    :param domain: Domain to check
    :param page_content_hash: String representing an MD5 hash of a page's content
    :return: None
    """

    # if the domain does not have a hash or the hash does not match:
    if 'website_hash' not in domain or domain['website_hash'] != page_content_hash:
        domain['website_hash'] = page_content_hash  # replace hash for the domain
        domain['content_status'] = 'extract'  # update content status
