import requests
import os
from utils.access_token import generate_access_token, upsert_access_token
from _globals import PAYLOAD_PASSWORD, DOMAIN

access_token_dict = generate_access_token(DOMAIN, PAYLOAD_PASSWORD)
os.environ["ACCESS_TOKEN"] = access_token_dict["access_token"]
upsert_access_token(access_token_dict["access_token"])
access_token = os.getenv("ACCESS_TOKEN")


def get_limits(domain: str, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{domain}/services/data/v59.0/limits", headers=headers)
    response.raise_for_status()
    return response.json()


limits = get_limits(DOMAIN, access_token)
print(limits["DailyApiRequests"])
