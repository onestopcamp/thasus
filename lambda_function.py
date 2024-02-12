import json
from datetime import datetime
# from dateutil.tz import gettz

from thasus.website_scanner import update_website_freshness


def lambda_handler(event, context):
    """Function to interface with AWS.

    :param event: The variable that interfaces with AWS. Passed in through lambda function.
    :param context: Unused.
    :returns: A dictionary containing a statusCode and a body of a JSON dump.
    """

    now = datetime.now()  # datetime object for the start of this function's operation
    start = now.timestamp()  # save the timestamp for when this function begins operation
    run_mode = event['run_mode']

    # exit early if not actually checking domains
    if run_mode != 'check_domains':
        return {
            'statusCode': 200,
            'body': json.dumps(f"Thasus tested at {now.timestamp()}")
        }

    print('Thasus running check')
    update_website_freshness()  # call freshness function
    print(f"Thasus ran in {datetime.now().timestamp() - start} millis")  # print how long the freshness function took to complete
    return {
        'statusCode': 200,
        'body': json.dumps(f"Thasus executed at {now.timestamp()}")
    }


# if this program is the main function, check domains
if __name__ == "__main__":
    event = {
        'run_mode': 'check_domains'
    }
    lambda_handler(event, None)
