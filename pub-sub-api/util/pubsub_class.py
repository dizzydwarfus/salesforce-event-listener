"""
PubSub.py

This file defines the class `PubSub`, which contains common functionality for
both publisher and subscriber clients.
"""

import io
import threading
from datetime import datetime
import json
from typing import Callable

import avro.io
import avro.schema
import certifi
import grpc

import util.pubsub_api_pb2 as pb2
import util.pubsub_api_pb2_grpc as pb2_grpc

from util.access_token import AccessToken

with open(certifi.where(), "rb") as f:
    secure_channel_credentials = grpc.ssl_channel_credentials(f.read())


class PubSub(object):
    """
    Class with helpers to use the Salesforce Pub/Sub API.

    The `PubSub` class contains methods to authenticate with the Salesforce
    via OAuth, retrieve a schema, and publish and subscribe to events.
    The `encode()` and `decode()` methods are helper functions to serialize and
    deserialize the payloads of events that clients will publish and receive
    using Avro. If you develop an implementation with a language other than
    Python, you will need to find an Avro library in that language that helps
    you encode and decode with Avro.

    When publishing an event, the plaintext payload needs to be Avro-encoded
    with the event schema for the API to accept it. When receiving an event, the
    Avro-encoded payload needs to be Avro-decoded with the event schema for you
    to read it in plaintext.

    The `subscribe()` method calls the Subscribe RPC defined in the proto file
    and accepts a client-defined callback to handle any events that are returned
    by the API. It uses a semaphore to prevent the Python client from closing
    the connection prematurely (this is due to the way Python's GRPC library is
    designed and may not be necessary for other languages--Java, for example,
    does not need this).

    The `fetch_req_stream()` method returns a FetchRequest stream for the
    Subscribe RPC.

    The `make_fetch_request()` method creates a FetchRequest per the proto file.

    The `get_schema_json()` method uses the GetSchema RPC to retrieve a schema
    given a schema ID.

    The `generate_producer_events()` method encodes the data to be sent in the
    event and creates a ProducerEvent per the proto file.

    The `publish()` method publishes events to the specified Platform Event topic.

    The `release_subscription_semaphore()` method releases the semaphore so that
    a new FetchRequest gets sent by `fetch_req_stream()`.

    The `auth()` method sends a login request to the Salesforce REST API to
    retrieve a session token. The session token is bundled with other identifying
    information to create a tuple of metadata headers, which are needed for every
    RPC call. Rewrite this method to use your own authentication method if you
    are not using client credentials OAuth method.

    The `get_topic()` method retrieves a topic given a topic name.

    Instantiate the class with a dictionary of arguments. The dictionary should
    contain the following keys:
    - url: The URL of the Salesforce instance
    - username (if using password-OAuth): The username of the Salesforce user
    - password (if using password-OAuth): The password of the Salesforce user
    - client_id (if using client credentials-OAuth): The client ID of the connected app
    - client_secret (if using client credentials-OAuth): The client secret of the connected app
    - grpcHost: The host of the gRPC server
    - grpcPort: The port of the gRPC server
    - topic: The name of the topic to subscribe to
    - apiVersion: The version of the Salesforce API to use

    """

    json_schema_dict = {}

    def __init__(self, argument_dict: dict, auth: AccessToken):
        self.url = argument_dict.get("url", "https://login.salesforce.com")
        self.username = argument_dict.get("username")
        self.password = argument_dict.get("password") + argument_dict.get(
            "security_token"
        )
        self.client_id = argument_dict.get("client_id")
        self.client_secret = argument_dict.get("client_secret")
        self.metadata = None
        grpc_host = argument_dict.get("grpcHost", "api.pubsub.salesforce.com")
        grpc_port = argument_dict.get("grpcPort", "7443")
        self.pubsub_url = grpc_host + ":" + grpc_port
        self.channel = grpc.secure_channel(self.pubsub_url, secure_channel_credentials)
        self.stub = pb2_grpc.PubSubStub(self.channel)
        self.access_token = None
        self.tenant_id = None
        self.pb2 = pb2
        self.topic_name = argument_dict.get("topic_name", "/data/ChangeEvents")
        self.apiVersion = argument_dict.get("apiVersion", "60.0")
        self.auth = auth
        """
        Semaphore used for subscriptions. This keeps the subscription stream open
        to receive events and to notify when to send the next FetchRequest.
        See Python Quick Start for more information. 
        https://developer.salesforce.com/docs/platform/pub-sub-api/guide/qs-python-quick-start.html
        """
        self.semaphore = threading.Semaphore(1)

    def authenticate(self, grant_type: str = "client_credentials"):
        """
        Sends a POST request to the Salesforce REST API to retrieve a access
        token. The session token is bundled with other identifying information
        to create a tuple of metadata headers, which are needed for every RPC
        call.
        """
        if grant_type == "password":
            payload = {
                "grant_type": grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password,
            }
        elif grant_type == "client_credentials":
            payload = {
                "grant_type": grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        else:
            raise ValueError(
                "Invalid grant type. Choose 'password' or 'client_credentials'"
            )

        instance = self.auth(domain=self.url, payload=payload)
        res = instance.generate_access_token()

        self.access_token = res["access_token"]
        self.tenant_id = res["id"].split("/")[-2]

        self.metadata = (
            ("accesstoken", f"Bearer {self.access_token}"),
            ("instanceurl", self.url),
            ("tenantid", self.tenant_id),
        )

    def release_subscription_semaphore(self):
        """
        Release semaphore so FetchRequest can be sent
        """
        self.semaphore.release()

    def make_fetch_request(
        self,
        topic: str,
        replay_type: str,
        replay_id: str,
        num_requested: int,
    ):
        """
        Creates a FetchRequest per the proto file.
        """
        replay_preset = None
        match replay_type:
            case "LATEST":
                replay_preset = pb2.ReplayPreset.LATEST
            case "EARLIEST":
                replay_preset = pb2.ReplayPreset.EARLIEST
            case "CUSTOM":
                replay_preset = pb2.ReplayPreset.CUSTOM
            case _:
                raise ValueError("Invalid Replay Type " + replay_type)

        try:
            replay_id = int(replay_id).to_bytes(10, "big")
            print(f"Replay ID is an integer: {replay_id}")

        except ValueError:
            replay_id = bytes.fromhex(replay_id)
            print(f"Replay ID is a hex string: {replay_id}")

        return pb2.FetchRequest(
            topic_name=topic,
            replay_preset=replay_preset,
            replay_id=replay_id,
            num_requested=num_requested,
        )

    def fetch_req_stream(
        self, topic: str, replay_type: str, replay_id: str, num_requested: int
    ):
        """
        Returns a FetchRequest stream for the Subscribe RPC.
        """
        while True:
            # Only send FetchRequest when needed. Semaphore release indicates need for new FetchRequest
            self.semaphore.acquire()
            print("Sending Fetch Request")
            yield self.make_fetch_request(
                topic=topic,
                replay_type=replay_type,
                replay_id=replay_id,
                num_requested=num_requested,
            )

    def encode(self, schema, payload):
        """
        Uses Avro and the event schema to encode a payload. The `encode()` and
        `decode()` methods are helper functions to serialize and deserialize
        the payloads of events that clients will publish and receive using
        Avro. If you develop an implementation with a language other than
        Python, you will need to find an Avro library in that language that
        helps you encode and decode with Avro. When publishing an event, the
        plaintext payload needs to be Avro-encoded with the event schema for
        the API to accept it. When receiving an event, the Avro-encoded payload
        needs to be Avro-decoded with the event schema for you to read it in
        plaintext.
        """
        schema = avro.schema.parse(schema)
        buf = io.BytesIO()
        encoder = avro.io.BinaryEncoder(buf)
        writer = avro.io.DatumWriter(schema)
        writer.write(payload, encoder)
        return buf.getvalue()

    def decode(self, schema, payload):
        """
        Uses Avro and the event schema to decode a serialized payload. The
        `encode()` and `decode()` methods are helper functions to serialize and
        deserialize the payloads of events that clients will publish and
        receive using Avro. If you develop an implementation with a language
        other than Python, you will need to find an Avro library in that
        language that helps you encode and decode with Avro. When publishing an
        event, the plaintext payload needs to be Avro-encoded with the event
        schema for the API to accept it. When receiving an event, the
        Avro-encoded payload needs to be Avro-decoded with the event schema for
        you to read it in plaintext.
        """
        schema = avro.schema.parse(schema)
        buf = io.BytesIO(payload)
        decoder = avro.io.BinaryDecoder(buf)
        reader = avro.io.DatumReader(schema)
        ret = reader.read(decoder)
        return ret

    def get_topic(self, topic_name):
        return self.stub.GetTopic(
            pb2.TopicRequest(topic_name=topic_name), metadata=self.metadata
        )

    def get_schema_json(self, schema_id):
        """
        Uses GetSchema RPC to retrieve schema given a schema ID.
        """
        # If the schema is not found in the dictionary, get the schema and store it in the dictionary
        if (
            schema_id not in self.json_schema_dict
            or self.json_schema_dict[schema_id] is None
        ):
            res = self.stub.GetSchema(
                pb2.SchemaRequest(schema_id=schema_id), metadata=self.metadata
            )
            self.json_schema_dict[schema_id] = res.schema_json

        return self.json_schema_dict[schema_id]

    def generate_producer_events(self, schema, schema_id):
        """
        Encodes the data to be sent in the event and creates a ProducerEvent per
        the proto file. Change the below payload to match the schema used.
        """
        payload = {
            "CreatedDate": int(datetime.now().timestamp()),
            "CreatedById": "005R0000000cw06IAA",  # Your user ID
            "textt__c": "Hello World",
        }
        req = {"schema_id": schema_id, "payload": self.encode(schema, payload)}
        return [req]

    def subscribe(
        self,
        topic: str,
        replay_type: str,
        replay_id: str,
        num_requested: int,
        callback: Callable,
    ):
        """
        Calls the Subscribe RPC defined in the proto file and accepts a
        client-defined callback to handle any events that are returned by the
        API. It uses a semaphore to prevent the Python client from closing the
        connection prematurely (this is due to the way Python's GRPC library is
        designed and may not be necessary for other languages--Java, for
        example, does not need this).
        """
        sub_stream = self.stub.Subscribe(
            self.fetch_req_stream(topic, replay_type, replay_id, num_requested),
            metadata=self.metadata,
        )
        print("> Subscribed to", topic)
        for event in sub_stream:
            callback(event, self)

    def publish(self, topic_name, schema, schema_id):
        """
        Publishes events to the specified Platform Event topic.
        """

        return self.stub.Publish(
            self.pb2.PublishRequest(
                topic_name=topic_name,
                events=self.generate_producer_events(schema, schema_id),
            ),
            metadata=self.metadata,
        )

    def read_event(self, event, bitmap_process):
        payloadbytes = event.event.payload
        schemaid = event.event.schema_id
        schema = self.stub.GetSchema(
            pb2.SchemaRequest(schema_id=schemaid), metadata=self.metadata
        ).schema_json

        decoded = self.decode(schema, payloadbytes)
        decoded["ChangeEventHeader"]["changedFields"] = bitmap_process(
            avro.schema.parse(schema),
            decoded["ChangeEventHeader"]["changedFields"],
        )
        decoded["ChangeEventHeader"]["nulledFields"] = bitmap_process(
            avro.schema.parse(schema),
            decoded["ChangeEventHeader"]["nulledFields"],
        )
        decoded["ChangeEventHeader"]["diffFields"] = bitmap_process(
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

    @staticmethod
    def return_event(decoded_event: dict):
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

    def store_replay_id(self, replay_id: bytes):
        """
        Store the replay ID in a file. This is used to resume
        receiving events from a specific point in time. The replay ID is
        returned in the FetchResponse and is used in the FetchRequest to
        retrieve events from a specific point in time.

        The replay ID is stored as a hexadecimal string in a file called
        `replay_id.txt`.

        When reading the replay ID from the file, it must be converted to
        bytes before being used in the FetchRequest. In python, this can be
        done with the `bytes.fromhex()` method.
        """
        with open("replay_id.txt", "wb") as file:
            # store as hexadecimal string
            file.write((replay_id.hex() + "\n").encode("utf-8"))

            # store as integer
            file.write((str(int.from_bytes(replay_id, "big"))).encode("utf-8"))

    def read_replay_id(self, filepath: str = "./replay_id.txt"):
        """
        Read the replay ID from a file. This is used to resume
        receiving events from a specific point in time. The replay ID is
        returned in the FetchResponse and is used in the FetchRequest to
        retrieve events from a specific point in time.

        The replay ID is stored as a hexadecimal string in a file called
        `replay_id.txt`.

        When reading the replay ID from the file, it must be converted to
        bytes before being used in the FetchRequest. In python, this can be
        done with the `bytes.fromhex()` method.
        """
        with open(filepath, "r") as file:
            replay_id = file.readlines()[1].strip()
            return replay_id
