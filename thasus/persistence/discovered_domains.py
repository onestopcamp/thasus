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
