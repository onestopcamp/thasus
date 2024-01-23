import hashlib
import traceback
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time

from thasus.persistence.discovered_domains import get_all_domains, update_domains

DAY_IN_MILLIS = 24 * 60 * 60 * 1000
WEEK_IN_MILLIS = 7 * DAY_IN_MILLIS

ignore_domains = [
    'tilthalliance.org'
]


def update_website_freshness(current_time_epoch):
    all_domains = get_all_domains()
    print(f"Found domains - {len(all_domains)}")

    updated_domains = list()
    for domain in all_domains:
        if is_website_content_fresh(domain, current_time_epoch):
            continue
        if domain['domain'] in ignore_domains:
            continue
        start = time.time()
        page_content = get_page_content(domain).encode('utf-8')
        content_extraction_time = time.time()
        page_content_hash = hashlib.md5(page_content).hexdigest()
        hash_time = time.time()
        if 'website_hash' not in domain or domain['website_hash'] != page_content_hash:
            domain['website_hash'] = page_content_hash
            domain['content_status'] = 'extract'

        domain['scanned_at'] = current_time_epoch
        print(f"{domain['domain_name']} extracted in "
              f"{content_extraction_time-start} "
              f"and hashed in {hash_time- content_extraction_time}"
              )
        updated_domains.append(domain)
    update_domains(updated_domains)


def is_website_content_fresh(domain, current_time_epoch):
    if 'scanned_at' not in domain:
        return False

    freshness_threshold = current_time_epoch - DAY_IN_MILLIS

    if domain['scanned_at'] <= freshness_threshold:
        return False


    return True


def get_page_content(domain):
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
    except Exception as e:
        print(f"Unable to get camp data for {domain['url']}")
        print(e)
        print(traceback.format_exc())
