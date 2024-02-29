import os
from dotenv import load_dotenv

load_dotenv()
print("Loaded .env file")

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
DOMAIN = os.getenv("DOMAIN")
SANDBOX_USERNAME = os.getenv("SANDBOX_USERNAME")
SANDBOX_PASSWORD = os.getenv("SANDBOX_PASSWORD")
USER_SECURITY_TOKEN = os.getenv("SECURITY_TOKEN")

PAYLOAD_CLIENT_CREDENTIALS = {
    "grant_type": "client_credentials",
    "client_id": CONSUMER_KEY,
    "client_secret": CONSUMER_SECRET,
}

PAYLOAD_PASSWORD = {
    "grant_type": "password",
    "client_id": CONSUMER_KEY,
    "client_secret": CONSUMER_SECRET,
    "username": SANDBOX_USERNAME,
    "password": SANDBOX_PASSWORD + USER_SECURITY_TOKEN,
}
