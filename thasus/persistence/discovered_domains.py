import boto3

DAY_IN_MILLIS = 24 * 60 * 60 * 1000
WEEK_IN_MILLIS = 7 * DAY_IN_MILLIS


def get_all_domains():
    """Fetches domains from an external table.

    This function accesses a DynamoDB resource and generates a table of discovered domains from it.
    For details on the full return value of dynamodb.scan(), see this link and scroll to "Response Structure":
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html

    :return: A dictionary containing only the Items field returned by the .scan() function, which is a list.
    """

    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')

    # response = discovered_domains.query(
    #     KeyConditionExpression=Key('scanned_at').eq('Arturus Ardvarkian') & Key('song').lt('C')
    # )
    return discovered_domains.scan()['Items']


def get_all_test_domains(current_time_epoch):
    """Test version of get_all_domains().

    Domain dictionary contains the following:
    'domain': String,
    'url': String,
    'domain_name': String,
    'scanned_at': int,
    'website_hash': String,
    'content_status': String

    :param current_time_epoch: Current time
    :return: list of test domain dictionaries
    """

    urls_to_scan = [
        'https://www.illuminationlearningstudio.com/summer-camps-2024/',
        'https://www.kongacademy.org/',  # https://www.kongacademy.org/in-person-classes ??
        'https://app.amilia.com/store/en/school-of-acrobatics-and-new-circus-arts/shop/programs/83792',
        'https://www.arenasports.net/schools-out-camp/',
        'http://pinnacleexplorations.org',
    ]
    test_domains = list()  # list containing all domains as dictionaries. only 5 since it's for testing

    # for each found domain, there are 6 fields to place data into, each self-explanatory. possibly more?
    # for the sake of testing, domains are truncated to make debugging easier
    for url in urls_to_scan:
        test_domains.append({
            'domain': url.replace('https://www.', '').replace('http://', '').replace('https://', '').split('/')[0],
            'url': url,
            'domain_name': url.replace('https://www.', '').replace('http://', '').replace('https://', '').split('/')[0],
            'scanned_at': current_time_epoch - DAY_IN_MILLIS - 1,
            'website_hash': None,
            'content_status': 'latest'
        })

    return test_domains


def update_domain_item(item):
    """Function to update a single item into the database

    :param item: An item to place into dynamodb
    :return: None
    """

    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')
    discovered_domains.put_item(
        Item=item
    )


def update_domains(updated_domains):
    """Function to update domains in the database.

    :param updated_domains: List of domains to update
    :return: None
    """

    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')
    # Function provided by AWS to batch write items to dynamoDB
    # See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/batch_writer.html
    with discovered_domains.batch_writer() as batch:
        for updated_domain in updated_domains:
            batch.put_item(
                Item=updated_domain
            )
