# Salesforce Event Listener in Python

This project enables real-time integration between Salesforce Event Bus and SAP Business One, leveraging Python for asynchronous event handling. Due to the lack of recent updates in `aiocometd` and `aiosfstream` libraries, which are crucial for connecting to the Salesforce Event Bus using the CometD protocol, this codebase includes modified versions of these libraries to ensure compatibility and stability with the latest Python versions and async features.

For integration architecture diagram, please refer to [conceptual diagram](docs/integration_architecture.md)
## Structure

The codebase is organized as follows:

- cometd_app/
  - `aiocometd/`: Modified library for CometD protocol support.
  - `aiosfstream/`: Modified library for Salesforce streaming API.
  - `utils/`: Utility functions and helpers.
  - `_globals.py`: Global configuration variables.
  - `test_sandbox.py`: Test script for sandbox environment interactions.
  - `create_custom_channel.py`: Script for creating custom channels in Salesforce.`
  - `listener.py`: Listener script for production environment events.
  - `consumer.py`: Consumer script for processing events.
  - `requirements.txt`: Lists Python package dependencies for the project.
- `docs/`: Contains documentation and diagrams.
- pub-sub-api/ (for future use, not currently implemented)
  -  `pubsub_api.proto`: Protocol buffer file for defining the API.
  -  `pubsub_api_pb2.py`: Generated Python file from the protocol buffer file.
  -  `pubsub_api_pb2_grpc.py`: Generated Python file from the protocol buffer file.
  -  `PubSubClient.py`: Client for interacting with the salesforce pub-sub API.
  - `requirements.txt`: Lists Python package dependencies for the project.
- `.gitignore`: Specifies intentionally untracked files to ignore.
- `Dockerfile`: Docker configuration for containerizing the application.

## Dependencies

This project's dependencies are listed in `requirements.txt`. Note that `aiocometd` and `aiosfstream` are not included as external dependencies but are part of the project structure and maintained locally.

## Setup

### Install dependencies:
```bash
pip install -r requirements.txt
```
Set up environment variables in .env file based on .env.example (if provided).

### Running the Application
To run the integration listener:

```bash
python listener.py
```

Or, for sandbox testing:

```bash
python test_sandbox.py
```

### To build and run the Docker container:

```bash
docker build -t sf-listener .
docker run -d --name sf-listener-app -e ENV_NAME=ENV_VALUE -e ... sf-listener 
```
## Note on Modified Libraries
Due to the inactive status of aiocometd and aiosfstream, necessary modifications were made to support the latest async features of Python and ensure compatibility with Salesforce's current API and Event Bus features. These libraries are maintained locally within this project to facilitate direct updates and customizations as required, avoiding dependency on potentially outdated or unsupported external libraries.

## Note on Pub-Sub API
The `pub-sub-api` directory contains a protocol buffer file for defining the API, as well as generated Python files for the API client. This is intended for future use and is not currently implemented in the project. This is the new API that Salesforce is moving towards, and it will replace the current CometD and Streaming API. The `pubsub_api.proto` file defines the API, and the `PubSubClient.py` file is the client for interacting with the Salesforce pub-sub API.