from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()


def create_config_from_env():
    return {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVER"),
        "security.protocol": os.getenv("SECRUITY_PROTOCOL"),
        "sasl.mechanisms": os.getenv("SASL_MECHANISM"),
        "sasl.username": os.getenv("SASL_USERNAME"),
        "sasl.password": os.getenv("SASL_PASSWORD"),
        "session.timeout.ms": os.getenv("SESSION_TIMEOUT_MS"),
    }


def send_message(topic, key, value):
    # producer and consumer code here
    config = create_config_from_env()

    # creates a new producer instance
    producer = Producer(config)

    # produces a sample message
    producer.produce(topic, key=key, value=value)
    print(f"Produced message to {topic} with key = {key:12}")

    # send any outstanding or buffered messages to the Kafka broker
    producer.flush()

    return


if __name__ == "__main__":
    config = create_config_from_env()
    print(config)
