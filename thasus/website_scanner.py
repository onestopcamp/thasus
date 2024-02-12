import hashlib
import traceback
from urllib.request import Request, urlopen

from dateutil.tz import gettz

from bs4 import BeautifulSoup
import io
import csv
from datetime import datetime

from thasus.persistence.tracked_domains import get_all_domains, update_domains, publish_csv
# from thasus.persistence.tracked_domains import get_all_test_domains

DAY_IN_SECS = 24 * 60 * 60
TOLERANCE = 1800  # 30 minutes

ignore_domains = [
    'tilthalliance.org'
]


def update_website_freshness():
    """Function to check whether a website is 'fresh', and if it is not, update it.

    Freshness is determined by whether a website has been updated in a certain amount of time.
    Additionally, a website can still be fresh even if it is old. Page content is taken as a string and hashed.
    If the hash matches, the website is still fresh, but its timestamp gets updated.

    :return: None
    """

    all_domains = get_all_domains()
    # all_domains = get_all_test_domains(current_time_epoch)
    domain_total = len(all_domains)
    print(f"Found domains - {domain_total}")

    updated_domains = list()  # list of domains that have been updated.
    failed_domains = list()  # list of domains that failed to be updated.

    # counters to help keep track of things
    domain_count = 0
    updated_count = 0
    failed_count = 0

    # convert time to human-readable in pst
    current_time_epoch = datetime.now().timestamp()  # get the current time to feed in to scans
    date_time = datetime.now(gettz('US/Pacific')).strftime("%d_%m_%yT%H-%M-%S")  # convert to human-readable in PST

    for domain in all_domains:
        domain_count += 1
        print(f"Processing domain {domain_count} of {domain_total}")
        # do not update domain if it is fresh
        if is_website_content_fresh(domain, int(current_time_epoch), date_time):  # convert epoch to int
            continue
        # do not update blacklisted domains
        if domain['domain'] in ignore_domains:
            continue

        start = datetime.now().timestamp()  # timestamp marker for when this domain started its scan
        page_result = get_page_content(domain)  # tuple containing page content and the result of the function

        # failure case.
        if page_result[1] is not None:
            domain['error_code'] = page_result[1]  # add exception text as a field to the domain. tuples SUCK
            failed_domains.append(domain)  # attach failed domain to the list
            failed_count += 1
            print(f"After this domain, {failed_count} have failed")
            continue
        page_content = page_result[0].encode('utf-8')  # String: obtain the page content
        content_extraction_time = datetime.now().timestamp()  # epoch marker for when the content finished extracting

        """ perhaps look into if there is a better way to do this; may be too complex or out of this program's scope.
            the upside is that a double-length md5 hash cannot possibly fail, and the super rare possibility of a hash
            collision is so small that it doesn't really affect the purpose of the hash.
            however, due to the volatile nature of websites, this may cause a large amount of false positives.
            depending on how expensive the scraper is, this may or may not be a big deal.
        """
        page_content_hash = hashlib.md5(page_content).hexdigest()  # calculate the hash based on the page content
        hash_time = datetime.now().timestamp()  # timestamp marker for when the hash finishes calculating
        check_hash(domain, page_content_hash)  # updates the hash and content status of a domain if necessary

        # print how long this operation took
        print(f"{domain['domain_name']} extracted in "
              f"{content_extraction_time - start} "
              f"and hashed in {hash_time - content_extraction_time}"
              )
        if domain['content_status'] == 'extract':
            updated_domains.append(domain)  # attach updated domain to the list
            updated_count += 1
            print(f"After this domain, {updated_count} have updated")

    update_domains(updated_domains)

    # update and publish a csv formatted string to the S3 bucket
    # make sure there are domains that need to be updated
    if len(updated_domains) > 0:
        update_string = convert_to_csv(updated_domains)
        publish_csv('updated_websites_' + date_time + '.csv', update_string)

    # make sure there are failed domains too
    if len(failed_domains) > 0:
        failed_string = convert_to_csv(failed_domains)
        publish_csv('failed_websites_' + date_time + '.csv', failed_string)

    print(f"Scanned websites: {domain_count}")
    print(f"Updated websites: {updated_count}")
    print(f"Failed websites: {failed_count}")


def is_website_content_fresh(domain, current_time_epoch, date_time):
    """Determines whether content is "fresh enough".

    A domain is considered not fresh if it was never scanned or was scanned at least one full day ago.
    Differences SMALLER than DAY_IN_SEC indicate freshness, since the offset is in the past. This means closer
    values are newer.
    This function also updates the domain's 'scanned_at' field if it is not fresh.
    A TOLERANCE value is used to give some grace to AWS Lambda functions not always running at exactly the same time.

    :param domain: domain to determine freshness of
    :param current_time_epoch: current UTC time epoch as an int
    :param date_time: string representing the date and time in PST
    :return: Boolean representing False for not fresh and True for fresh.
    """

    # convert datetime into a string that's more human-readable and doesn't need to abide by file system restrictions
    dt = date_time.replace("_", "/")
    dt = dt.replace("-", ":")

    if 'scanned_at' not in domain:
        domain['scanned_at'] = current_time_epoch  # update timestamp for domain
        domain['scanned_datetime'] = dt  # update datetime for domain
        return False

    # if it's more than a day old, it is not fresh
    # TOLERANCE value is added so that a daily scan is more likely to be effective. theoretically, a domain scanned
    # yesterday should be 24 hours old, give or take; reducing the required difference to 23.5 hours might be sufficient
    freshness_threshold = current_time_epoch - DAY_IN_SECS + TOLERANCE

    # if a day old or more, it is not fresh
    if int(domain['scanned_at']) <= freshness_threshold:  # shouldn't need typecast
        domain['scanned_at'] = current_time_epoch  # update timestamp for domain
        domain['scanned_datetime'] = dt  # update datetime for domain
        return False

    # if it is fresh, simply return. scan timestamps will not be updated
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
        page = urlopen(req)  # May raise URLError or HTTPError. Returns a redirected url object.
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


def convert_to_csv(domains):
    """Converts a list of domains into a reformatted string that can be used as a CSV file.

    :param domains: A list of domains.
    :return: A string containing a reformatted domain list.
    """

    headers = list(domains[0].keys())  # create headers based on first domain. all headers are expected to be the same

    file = io.StringIO()  # Spoofs a file since lambda does not have file directories

    # creates a CSV string for updated domains using the spoofed file and DictWriter
    # don't raise an error if website hash doesn't exist. preferably fill it with nothing
    writer = csv.DictWriter(file, headers, dialect='unix', restval="", extrasaction='ignore')
    writer.writeheader()
    writer.writerows(domains)

    return file.getvalue()
