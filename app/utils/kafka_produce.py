from confluent_kafka import Producer, Consumer
import os
from dotenv import load_dotenv

load_dotenv()


def read_config(config_file="./client.properties"):
    # reads the client configuration from client.properties
    # and returns it as a key-value map
    config = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split("=", 1)
                config[parameter] = value.strip()
    return config


def create_config_from_env():
    return {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVER"),
        "security.protocol": os.getenv("SECRUITY_PROTOCOL"),
        "sasl.mechanisms": os.getenv("SASL_MECHANISM"),
        "sasl.username": os.getenv("SASL_USERNAME"),
        "sasl.password": os.getenv("SASL_PASSWORD"),
        "session.timeout.ms": os.getenv("SESSION_TIMEOUT_MS"),
    }


def test_send(config_file, topic, key, value):
    # producer and consumer code here
    config = read_config(config_file)

    # creates a new producer instance
    producer = Producer(config)

    # produces a sample message
    producer.produce(topic, key=key, value=value)
    print(f"Produced message to topic {topic}: key = {key:12} value = {value:12}")

    # send any outstanding or buffered messages to the Kafka broker
    producer.flush()

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
                    f"Consumed message from topic {topic}: key = {key:12} value = {value:12}"
                )
    except KeyboardInterrupt:
        pass
    finally:
        # closes the consumer connection
        consumer.close()


def send_message(config_file, topic, key, value):
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
    # config = read_config("app/utils/client.properties")
    config = create_config_from_env()
    print(config)

    # test_send(
    #     config_file="app/utils/client.properties",
    #     topic="account_updated",
    #     key="key",
    #     value="value",
    # )
