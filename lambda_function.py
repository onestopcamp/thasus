import json
from datetime import datetime
# from dateutil.tz import gettz
import time

from thasus.website_scanner import update_website_freshness


def lambda_handler(event, context):
    start = time.time()
    run_mode = event['run_mode']

    if run_mode != 'check_domains':
        return {
            'statusCode': 200,
            'body': json.dumps(f"Thasus tested at {get_now()}")
        }

    print('Thasus running check')
    current_time_epoch = int(time.time())
    update_website_freshness(current_time_epoch)
    print(f"Thasus ran in {time.time() - start} millis")
    return {
        'statusCode': 200,
        'body': json.dumps(f"Thasus executed at {get_now()}")
    }


def get_now():
    # now_pacific = datetime.now(gettz('US/Pacific'))
    # return now_pacific.isoformat(timespec='seconds')
    return int(time.time())


if __name__ == "__main__":
    event = {
        'run_mode': 'check_domains'
    }
    lambda_handler(event, None)

