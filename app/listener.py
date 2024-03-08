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
from utils.kafka_produce import send_message, read_config
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
    reconnect_attempts = 0
    # connect to your Salesforce Org (Production or Developer org)
    while True:
        try:
            async with SalesforceStreamingClient(
                domain=PROD_DOMAIN,
                consumer_key=PROD_CONSUMER_KEY,
                consumer_secret=PROD_CONSUMER_SECRET,
                sandbox=False,
                username=PROD_USERNAME,
                password=PROD_PASSWORD + PROD_SECURITY_TOKEN,
            ) as client:
                reconnect_attempts = (
                    0  # resets reconnect attempts upon successful connection
                )

                # subscribe to the platform event using CometD
                await client.subscribe("/data/ChangeEvents")
                access_token = client.auth.__dict__["access_token"]
                domain = client.auth.__dict__["instance_url"]
                # listen for incoming messages
                message_count = 0
                async for message in client:
                    value = json.dumps(
                        message["data"]["payload"], indent=4, sort_keys=True
                    )
                    key = str(message["data"]["event"]["replayId"])
                    print(f"Key: {str(key)}")
                    print(f"Value: {value}")

                    # # Send to Kafka
                    send_message(
                        config_file="app/utils/client.properties",
                        topic="account_updated",
                        key=key,
                        value=value,
                    )

                    message_count += 1
                    print(f"Message Count: {message_count}")

                    # Get limits
                    if message_count % 5 == 0:
                        limits = get_limits(domain=domain, access_token=access_token)
                        print(
                            f'{limits["DailyDeliveredPlatformEvents"]}\n{limits["DailyApiRequests"]}'
                        )

        except Exception as e:
            print(f"An error occurred: {e}")
            reconnect_attempts += 1
            wait_time = min(
                reconnect_attempts * 2, 30
            )  # Exponential backoff with a cap
            print(f"Waiting {wait_time} seconds before reattempting connection...")
            await asyncio.sleep(wait_time)  # Wait before attempting to reconnect


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
