# Salesforce Event Listener in Python

This project enables real-time integration between Salesforce Event Bus and SAP Business One, leveraging Python for asynchronous event handling. Due to the lack of recent updates in `aiocometd` and `aiosfstream` libraries, which are crucial for connecting to the Salesforce Event Bus using the CometD protocol, this codebase includes modified versions of these libraries to ensure compatibility and stability with the latest Python versions and async features.

For integration architecture diagram, please refer to [conceptual diagram](docs/integration_architecture.md)
## Structure

The codebase is organized as follows:

- `aiocometd/`: Modified library for CometD protocol support.
- `aiosfstream/`: Modified library for Salesforce streaming API.
- `salesforce_api_311/`: Contains modules for interacting with Salesforce API v3.11.
- `SAP_magic/`: Modules for handling SAP Business One integration logic.
- `utils/`: Utility functions and helpers.
- `_globals.py`: Global configuration variables.
- `.env`: Environment variables for storing sensitive information (not tracked by Git).
- `.gitignore`: Specifies intentionally untracked files to ignore.
- `Dockerfile`: Docker configuration for containerizing the application.
- `requirements.txt`: Lists Python package dependencies for the project.
- `listener.py`: Listener script for production environment events.
- `test_sandbox.py`: Test script for sandbox environment interactions.

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
python test_prod.py
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