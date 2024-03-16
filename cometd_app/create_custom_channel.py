from utils.access_token import AccessToken
from _globals import PROD_DOMAIN, PROD_PAYLOAD_CLIENT_CREDENTIALS
import json
import requests


def create_custom_channel(access_token):
    create_channel_url = (
        PROD_DOMAIN + "/services/data/v59.0/tooling/sobjects/PlatformEventChannel"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "FullName": "MasterDataSync__chn",
        "Metadata": {
            "channelType": "data",
            "label": "Custom Channel for Master Data Sync",
        },
    }
    requests.post(create_channel_url, headers=headers, data=payload)


def get_channel_info(access_token):
    get_channel_url = f"{PROD_DOMAIN}/services/data/v59.0/tooling/query/?q=SELECT+Id,DeveloperName,MasterLabel,ChannelType+FROM+PlatformEventChannel"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(get_channel_url, headers=headers)
    return response.json()


if __name__ == "__main__":
    instance = AccessToken(PROD_DOMAIN, PROD_PAYLOAD_CLIENT_CREDENTIALS)
    access_token = instance.generate_access_token()
    print(access_token, "\n")
    # print("Creating custom channel")
    # create_custom_channel(access_token["access_token"])
    # print("Custom channel created\n")

    # Request from channel data to see if channel is created
    print("Requesting channel data")
    channel_info = get_channel_info(access_token["access_token"])
    print(channel_info)
