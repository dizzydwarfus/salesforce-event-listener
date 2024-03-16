import grpc
import threading
import io
import pubsub_api_pb2 as pb2
import pubsub_api_pb2_grpc as pb2_grpc
import avro.schema
import avro.io
import time
import certifi
import json
import os
from access_token import AccessToken
from dotenv import load_dotenv
from bitstring import BitArray
import sys


load_dotenv()

semaphore = threading.Semaphore(1)


def read_replay_id(filepath: str = "replay_id.txt"):
    with open(filepath, "r") as file:
        latest_replay_id = file.read()
        latest_replay_id = bytes.fromhex(latest_replay_id)
        return latest_replay_id


def fetchReqStream(topic, replay_id=None):
    replay_preset = pb2.ReplayPreset.CUSTOM if replay_id else pb2.ReplayPreset.LATEST
    print(replay_preset)
    while True:
        semaphore.acquire()
        yield pb2.FetchRequest(
            topic_name=topic,
            replay_preset=replay_preset,
            num_requested=10,
            replay_id=replay_id,
        )


def decode(schema, payload):
    schema = avro.schema.parse(schema)
    buf = io.BytesIO(payload)
    decoder = avro.io.BinaryDecoder(buf)
    reader = avro.io.DatumReader(schema)
    ret = reader.read(decoder)
    return ret


def convert_hexbinary_to_bitset(bitmap):
    bit_array = BitArray(hex=bitmap[2:])
    binary_string = bit_array.bin
    return binary_string[::-1]


# Find the positions of 1 in the bit string
def find(to_find, binary_string):
    return [i for i, x in enumerate(binary_string) if x == to_find]


def get_fieldnames_from_bitstring(bitmap, avro_schema: avro.schema.Schema):
    bitmap_field_name = []
    fields_list = list(avro_schema.fields)
    binary_string = convert_hexbinary_to_bitset(bitmap)
    indexes = find("1", binary_string)
    for index in indexes:
        bitmap_field_name.append(fields_list[index].name)
    return bitmap_field_name


# Get the value type of an "optional" schema, which is a union of [null, valueSchema]
def get_value_schema(parent_field):
    if parent_field.type == "union":
        schemas = parent_field.schemas
        if len(schemas) == 2 and schemas[0].type == "null":
            return schemas[1]
        if len(schemas) == 2 and schemas[0].type == "string":
            return schemas[1]
        if (
            len(schemas) == 3
            and schemas[0].type == "null"
            and schemas[1].type == "string"
        ):
            return schemas[2]
    return parent_field


def append_parent_name(parent_field_name, full_field_names):
    for index in range(len(full_field_names)):
        full_field_names[index] = parent_field_name + "." + full_field_names[index]
    return full_field_names


def process_bitmap(avro_schema: avro.schema.Schema, bitmap_fields: list):
    fields = []
    if len(bitmap_fields) != 0:
        # replace top field level bitmap with list of fields
        if bitmap_fields[0].startswith("0x"):
            bitmap = bitmap_fields[0]
            fields = fields + get_fieldnames_from_bitstring(bitmap, avro_schema)
            bitmap_fields.remove(bitmap)
        # replace parentPos-nested Nulled BitMap with list of fields too
        if len(bitmap_fields) != 0 and "-" in str(bitmap_fields[-1]):
            for bitmap_field in bitmap_fields:
                if bitmap_field is not None and "-" in str(bitmap_field):
                    bitmap_strings = bitmap_field.split("-")
                    # interpret the parent field name from mapping of parentFieldPos -> childFieldbitMap
                    parent_field = avro_schema.fields[int(bitmap_strings[0])]
                    child_schema = get_value_schema(parent_field.type)
                    # make sure we're really dealing with compound field
                    if child_schema.type is not None and child_schema.type == "record":
                        nested_size = len(child_schema.fields)
                        parent_field_name = parent_field.name
                        # interpret the child field names from mapping of parentFieldPos -> childFieldbitMap
                        full_field_names = get_fieldnames_from_bitstring(
                            bitmap_strings[1], child_schema
                        )
                        full_field_names = append_parent_name(
                            parent_field_name, full_field_names
                        )
                        if len(full_field_names) > 0:
                            # when all nested fields under a compound got nulled out at once by customer, we recognize the top level field instead of trying to list every single nested field
                            fields = fields + full_field_names
    return fields


def read_event(
    authmetadata,
    stub,
    received_event,
):
    payloadbytes = received_event.event.payload
    schemaid = received_event.event.schema_id
    schema = stub.GetSchema(
        pb2.SchemaRequest(schema_id=schemaid), metadata=authmetadata
    ).schema_json

    decoded = decode(schema, payloadbytes)
    decoded["ChangeEventHeader"]["changedFields"] = process_bitmap(
        avro.schema.parse(schema),
        decoded["ChangeEventHeader"]["changedFields"],
    )
    decoded["ChangeEventHeader"]["nulledFields"] = process_bitmap(
        avro.schema.parse(schema),
        decoded["ChangeEventHeader"]["nulledFields"],
    )
    decoded["ChangeEventHeader"]["diffFields"] = process_bitmap(
        avro.schema.parse(schema),
        decoded["ChangeEventHeader"]["diffFields"],
    )

    if __debug__:
        print("Got an event!\n", json.dumps(decoded, indent=2))

        if "ChangeEventHeader" in decoded:
            print("Change Type: " + decoded["ChangeEventHeader"]["changeType"])
            print("=========== Changed Fields =============")
            print(decoded["ChangeEventHeader"]["changedFields"])
            print("=========================================")
    return decoded


def process_event(decoded_event):
    print("Processing event...\n")

    changed_fields = decoded_event["ChangeEventHeader"]["changedFields"]
    nulled_fields = decoded_event["ChangeEventHeader"]["nulledFields"]
    diff_fields = decoded_event["ChangeEventHeader"]["diffFields"]

    # filter decoded dictionary to only include fields that have changed, nulled, or diffed or are part of the ChangeEventHeader
    processed_event = {
        k: v
        for k, v in decoded_event.items()
        if k == "ChangeEventHeader"
        or k in changed_fields
        or k in diff_fields
        or k in nulled_fields
    }

    return processed_event


def get_authmetadata():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("PROD_CONSUMER_KEY"),
        "client_secret": os.getenv("PROD_CONSUMER_SECRET"),
    }
    domain = os.getenv("PROD_DOMAIN")
    instance = AccessToken(domain=domain, payload=payload)
    res = instance.generate_access_token()
    authmetadata = (
        ("accesstoken", f"Bearer {res['access_token']}"),
        ("instanceurl", domain),
        ("tenantid", res["id"].split("/")[-2]),
    )
    return authmetadata


def subscribe_with_retry(
    topic: str,
    authmetadata: tuple,
):
    attempt = 0
    wait_time = 1  # Start with 1 second wait time
    # replay_id = read_replay_id()
    # print(f"self initialized replay_id: {replay_id}")
    while True:
        if len(sys.argv) > 1:
            try:
                replay_id = read_replay_id(sys.argv[1])
                print(f"manual input {replay_id}")
            except Exception as e:
                print(
                    "Error reading replay_id from file, please provide a new replay_id filepath or use the default latest replay_id."
                )
                new_input = input("Use default latest replay_id? (y/n): ").lower()
                if new_input == "y":
                    sys.argv[1] = None
                elif new_input == "n":
                    sys.argv[1] = input("Enter new replay_id filepath: ")
                    replay_id = read_replay_id(sys.argv[1])
                else:
                    print("Invalid input, defaulting to latest replay_id")
                    replay_id = None
        else:
            print("No replay_id provided, defaulting to latest replay_id")
            replay_id = None

        try:
            with open(certifi.where(), "rb") as f:
                creds = grpc.ssl_channel_credentials(f.read())
            with grpc.secure_channel(
                "api.pubsub.salesforce.com:7443", creds
            ) as channel:
                stub = pb2_grpc.PubSubStub(channel)

                # Use a context manager for the subscription stream
                print("Subscribing to " + topic)
                substream = stub.Subscribe(
                    fetchReqStream(topic, replay_id=replay_id), metadata=authmetadata
                )

                for event in substream:
                    # Process each event
                    if event.events:
                        semaphore.release()
                        print("Number of events received: ", len(event.events))
                        for received_event in event.events:
                            event_read = read_event(authmetadata, stub, received_event)
                            processed_event = process_event(event_read)
                            print(json.dumps(processed_event, indent=2))

                        replay_id = (
                            event.latest_replay_id
                        )  # Update replay_id with the latest from the event
                        print(
                            f"replay_id bytes: {replay_id}\nreplay_id hex: {replay_id.hex()}"
                        )
                        # Persist the replay_id to a file or database
                        with open("replay_id.txt", "w") as file:
                            file.write(replay_id.hex())
                    else:
                        print(
                            "[",
                            time.strftime("%b %d, %Y %I:%M%p %Z"),
                            "] The subscription is active.",
                        )

                    # If subscription and processing are successful, reset attempt and wait_time in case of future retries
                    attempt = 0
                    wait_time = 1
                    print(f"retry attempts: {attempt}, wait time: {wait_time}")

        except grpc.RpcError as e:
            print(
                f"RPC error encountered: {e}{e.code()}. Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)
            wait_time *= 2
            wait_time = min(wait_time, 30)  # Cap the wait time at 30 seconds
            attempt += 1

        except TimeoutError as e:
            print(f"Timeout error encountered: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2
            wait_time = min(wait_time, 30)
            attempt += 1

        except Exception as e:
            print(f"Error encountered: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2
            wait_time = min(wait_time, 30)
            attempt += 1


if __name__ == "__main__":
    authmetadata = get_authmetadata()
    subscribe_with_retry("/data/ChangeEvents", authmetadata)

    # print(read_replay_id(sys.argv[1]))
