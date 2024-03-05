# import os
import requests
import json
import time

# Async libraries
import asyncio
from aiosfstream import SalesforceStreamingClient

# Internal imports
from _globals import (
    PROD_CONSUMER_KEY,
    PROD_CONSUMER_SECRET,
    PROD_USERNAME,
    PROD_PASSWORD,
    PROD_SECURITY_TOKEN,
    PROD_DOMAIN,
    # PROD_PAYLOAD_CLIENT_CREDENTIALS,
)
# from utils.access_token import AccessToken


def get_limits(domain: str, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{domain}/services/data/v59.0/limits", headers=headers)
    response.raise_for_status()
    return response.json()


def get_platform_events_usage(domain: str, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{domain}/services/data/v59.0/query?q=SELECT+Name+,+StartDate+,+EndDate+,+Value+FROM+PlatformEventUsageMetric",
        headers=headers,
    )
    response.raise_for_status()
    return json.dumps(obj=response.json(), indent=4)


async def stream_events():
    # connect to your Salesforce Org (Production or Developer org)
    async with SalesforceStreamingClient(
        domain=PROD_DOMAIN,
        consumer_key=PROD_CONSUMER_KEY,
        consumer_secret=PROD_CONSUMER_SECRET,
        sandbox=False,
        username=PROD_USERNAME,
        password=PROD_PASSWORD + PROD_SECURITY_TOKEN,
    ) as client:
        # subscribe to the platform event using CometD
        await client.subscribe("/data/ChangeEvents")
        access_token = client.auth.__dict__["access_token"]
        domain = client.auth.__dict__["instance_url"]
        # listen for incoming messages
        message_count = 0
        async for message in client:
            pretty_data = json.dumps(message, indent=4, sort_keys=True)
            print(f"{pretty_data}")
            message_count += 1
            print(f"Message Count: {message_count}")
            if message_count % 5 == 0:
                limits = get_limits(domain=domain, access_token=access_token)
                print(
                    f'{limits["DailyDeliveredPlatformEvents"]}\n{limits["DailyApiRequests"]}'
                )


if __name__ == "__main__":
    try:
        start = time.perf_counter()
        print(f"Started at {start}")
        asyncio.run(stream_events())
    except Exception as e:
        print(e)
        end = time.perf_counter()
        print(f"Finished at {end}")
        print(f"Time elapsed: {(end - start):.2f} minutes.")
    # instance = AccessToken(domain=PROD_DOMAIN, payload=PROD_PAYLOAD_CLIENT_CREDENTIALS)
    # instance.generate_access_token()
    # print(get_stream_events(domain=instance.domain, access_token=instance.access_token))
    # limits = get_limits(instance.domain, instance.access_token)
    # print(limits)
