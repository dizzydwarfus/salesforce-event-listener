import os
import time
import json
from dotenv import load_dotenv

from util.access_token import AccessToken
from util.pubsub_class import PubSub
from util.ChangeEventHeaderUtility import process_bitmap

load_dotenv()

argument_dict = {
    "url": os.environ.get("PROD_DOMAIN"),
    "client_id": os.environ.get("PROD_CONSUMER_KEY"),
    "client_secret": os.environ.get("PROD_CONSUMER_SECRET"),
    "username": os.environ.get("PROD_USERNAME"),
    "password": os.environ.get("PROD_PASSWORD"),
    "security_token": os.environ.get("PROD_SECURITY_TOKEN"),
    "grpc_host": os.environ.get("GRPC_HOST"),
    "grpc_port": os.environ.get("GRPC_PORT"),
    "topic_name": os.environ.get("TOPIC_NAME"),
}


def process_event(event, pubsub):
    if event.events:
        print("Number of events received in FetchResponse: ", len(event.events))
        # If all requested events are delivered, release the semaphore
        # so that a new FetchRequest gets sent by `PubSub.fetch_req_stream()`.
        if event.pending_num_requested == 0:
            pubsub.release_subscription_semaphore()

        for evt in event.events:
            event_read = pubsub.read_event(evt, process_bitmap)
            event_read = pubsub.return_event(event_read)
            print(json.dumps(event_read, indent=2))

        pubsub.store_replay_id(event.latest_replay_id)

    else:
        print(
            "[",
            time.strftime("%b %d, %Y %I:%M%p %Z"),
            "] The subscription is active.",
        )
        raise TimeoutError("No events received")


if __name__ == "__main__":
    wait_time = 1
    attempt = 0
    while True:
        try:
            pubsub = PubSub(argument_dict=argument_dict, auth=AccessToken)
            pubsub.authenticate()

            try:
                replay_id = pubsub.read_replay_id()
                replay_type = "CUSTOM"
                # print(bytes.fromhex(replay_id))
                # print(int(replay_id).to_bytes(10, "big"))

            except FileNotFoundError:
                replay_id = ""
                replay_type = "LATEST"
                print(replay_id)

            pubsub.subscribe(
                topic=pubsub.topic_name,
                replay_type=replay_type,
                replay_id=replay_id,
                num_requested=10,
                callback=process_event,
            )
            wait_time = 1
            attempt = 0

        except Exception as e:
            print(f"Error encountered: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2  # Exponential backoff
            wait_time = min(wait_time, 30)  # Cap the wait time at 30 seconds
            attempt += 1  # Increment the retry attempt
            continue
