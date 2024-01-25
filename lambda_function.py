import json
# from datetime import datetime
# from dateutil.tz import gettz
import time

from thasus.website_scanner import update_website_freshness


def lambda_handler(event, context):
    """Function to interface with AWS... I think.

    :param event: Seems to be the variable that interfaces with AWS.
    :param context: Unused.
    :returns: A dictionary containing a statusCode and a body of a JSON dump.
    """

    start = time.time()  # save the timestamp for when this function begins operation
    run_mode = event['run_mode']

    # exit early if not actually checking domains
    if run_mode != 'check_domains':
        return {
            'statusCode': 200,
            'body': json.dumps(f"Thasus tested at {get_now()}")
        }

    print('Thasus running check')
    current_time_epoch = int(time.time())  # current timestamp as a value to insert as freshness
    update_website_freshness(current_time_epoch)  # call freshness function for the "current" time
    print(f"Thasus ran in {time.time() - start} millis")  # print how long the freshness function took to complete
    return {
        'statusCode': 200,
        'body': json.dumps(f"Thasus executed at {get_now()}")
    }


def get_now():
    """Grabs current time.

    :return: 'time', as int
    """

    # now_pacific = datetime.now(gettz('US/Pacific'))
    # return now_pacific.isoformat(timespec='seconds')
    return int(time.time())


# if this program is the main function, check domains
if __name__ == "__main__":
    event = {
        'run_mode': 'check_domains'
    }
    lambda_handler(event, None)
