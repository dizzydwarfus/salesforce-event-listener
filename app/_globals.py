import os
from dotenv import load_dotenv

load_dotenv()
print("Loaded .env file")

SANDBOX_CONSUMER_KEY = os.getenv("SANDBOX_CONSUMER_KEY")
SANDBOX_CONSUMER_SECRET = os.getenv("SANDBOX_CONSUMER_SECRET")
SANDBOX_DOMAIN = os.getenv("SANDBOX_DOMAIN")
SANDBOX_USERNAME = os.getenv("SANDBOX_USERNAME")
SANDBOX_PASSWORD = os.getenv("SANDBOX_PASSWORD")
SANDBOX_SECURITY_TOKEN = os.getenv("SANDBOX_SECURITY_TOKEN")

PROD_CONSUMER_KEY = os.getenv("PROD_CONSUMER_KEY")
PROD_CONSUMER_SECRET = os.getenv("PROD_CONSUMER_SECRET")
PROD_DOMAIN = os.getenv("PROD_DOMAIN")
PROD_USERNAME = os.getenv("PROD_USERNAME")
PROD_PASSWORD = os.getenv("PROD_PASSWORD")
PROD_SECURITY_TOKEN = os.getenv("PROD_SECURITY_TOKEN")

try:
    SANDBOX_PAYLOAD_CLIENT_CREDENTIALS = {
        "grant_type": "client_credentials",
        "client_id": SANDBOX_CONSUMER_KEY,
        "client_secret": SANDBOX_CONSUMER_SECRET,
    }
    SANDBOX_PAYLOAD_PASSWORD = {
        "grant_type": "password",
        "client_id": SANDBOX_CONSUMER_KEY,
        "client_secret": SANDBOX_CONSUMER_SECRET,
        "username": SANDBOX_USERNAME,
        "password": SANDBOX_PASSWORD + SANDBOX_SECURITY_TOKEN,
    }
except Exception as e:
    print("Parsing environment variables Error:", e)
    pass

try:
    PROD_PAYLOAD_CLIENT_CREDENTIALS = {
        "grant_type": "client_credentials",
        "client_id": PROD_CONSUMER_KEY,
        "client_secret": PROD_CONSUMER_SECRET,
    }

    PROD_PAYLOAD_PASSWORD = {
        "grant_type": "password",
        "client_id": PROD_CONSUMER_KEY,
        "client_secret": PROD_CONSUMER_SECRET,
        "username": PROD_USERNAME,
        "password": PROD_PASSWORD + PROD_SECURITY_TOKEN,
    }
except Exception as e:
    print("Parsing environment variables Error:", e)
    pass
