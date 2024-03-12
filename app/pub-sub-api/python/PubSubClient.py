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

load_dotenv()

semaphore = threading.Semaphore(1)

latest_replay_id = None


def fetchReqStream(topic):
    while True:
        semaphore.acquire()
        yield pb2.FetchRequest(
            topic_name=topic, replay_preset=pb2.ReplayPreset.LATEST, num_requested=10
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


with open(certifi.where(), "rb") as f:
    creds = grpc.ssl_channel_credentials(f.read())
with grpc.secure_channel("api.pubsub.salesforce.com:7443", creds) as channel:
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("PROD_CONSUMER_KEY"),
        "client_secret": os.getenv("PROD_CONSUMER_SECRET"),
    }
    domain = os.getenv("PROD_DOMAIN")
    instance = AccessToken(domain=domain, payload=payload)
    res = instance.generate_access_token()
    # Optionally, print the content field returned
    # print(res)

    authmetadata = (
        ("accesstoken", f"Bearer {res['access_token']}"),
        ("instanceurl", domain),
        ("tenantid", res["id"].split("/")[-2]),
    )

    stub = pb2_grpc.PubSubStub(channel)

    mysubtopic = "/data/ChangeEvents"
    print("Subscribing to " + mysubtopic)
    substream = stub.Subscribe(fetchReqStream(mysubtopic), metadata=authmetadata)
    for event in substream:
        if event.events:
            semaphore.release()
            print("Number of events received: ", len(event.events))

            payloadbytes = event.events[0].event.payload
            schemaid = event.events[0].event.schema_id
            schema = stub.GetSchema(
                pb2.SchemaRequest(schema_id=schemaid), metadata=authmetadata
            ).schema_json

            decoded = decode(schema, payloadbytes)

            print("Got an event!", json.dumps(decoded, indent=2))

            if "ChangeEventHeader" in decoded:
                changed_fields = decoded["ChangeEventHeader"]["changedFields"]
                print("Change Type: " + decoded["ChangeEventHeader"]["changeType"])
                print("=========== Changed Fields =============")
                print(process_bitmap(avro.schema.parse(schema), changed_fields))
                print("=========================================")

        else:
            print(
                "[",
                time.strftime("%b %d, %Y %I:%M%p %Z"),
                "] The subscription is active.",
            )
        latest_replay_id = event.latest_replay_id
