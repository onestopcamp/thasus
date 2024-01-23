import boto3

DAY_IN_MILLIS = 24 * 60 * 60 * 1000
WEEK_IN_MILLIS = 7 * DAY_IN_MILLIS


def get_all_domains():
    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')

    # response = discovered_domains.query(
    #     KeyConditionExpression=Key('scanned_at').eq('Arturus Ardvarkian') & Key('song').lt('C')
    # )
    return discovered_domains.scan()['Items']


def get_all_test_domains(current_time_epoch):
    urls_to_scan = [
        'https://www.illuminationlearningstudio.com/summer-camps-2024/',
        'https://www.kongacademy.org/',
        'https://app.amilia.com/store/en/school-of-acrobatics-and-new-circus-arts/shop/programs/83792',
        'https://www.arenasports.net/schools-out-camp/',
        'http://pinnacleexplorations.org',
    ]
    test_domains = list()

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
    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')
    discovered_domains.put_item(
        Item=item
    )


def update_domains(updated_domains):
    dynamodb = boto3.resource('dynamodb')
    discovered_domains = dynamodb.Table('discovered_domains')
    with discovered_domains.batch_writer() as batch:
        for updated_domain in updated_domains:
            batch.put_item(
                Item=updated_domain
            )
