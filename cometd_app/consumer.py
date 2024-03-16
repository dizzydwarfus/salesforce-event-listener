from confluent_kafka import Consumer
import json
import os
from dotenv import load_dotenv

from utils.kafka_produce import create_config_from_env

load_dotenv()


def consume(
    config,
    topic,
):
    # sets the consumer group ID and offset
    config["group.id"] = "python-group-1"
    config["auto.offset.reset"] = "earliest"

    # creates a new consumer and subscribes to your topic
    consumer = Consumer(config)
    consumer.subscribe([topic])
    try:
        while True:
            # consumer polls the topic and prints any incoming messages
            msg = consumer.poll(1.0)
            if msg is not None and msg.error() is None:
                key = msg.key().decode("utf-8")
                value = msg.value().decode("utf-8")
                print(
                    f"Consumed message from topic {topic}:\nkey = {key:12}\nvalue = {value:12}"
                )
    except KeyboardInterrupt:
        pass
    finally:
        # closes the consumer connection
        consumer.close()


if __name__ == "__main__":
    config = create_config_from_env()
    consume(config, "account_updated")
