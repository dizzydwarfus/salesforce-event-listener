import json


def transform_message(message):
    # transform the message here
    key = message["data"]["event"]["replayId"]
    value = message["data"]["payload"]
    # change_type = value["ChangeEventHeader"]["changeType"]
    # records_updated = value["ChangeEventHeader"]["recordIds"]

    # value = {
    #     "key": key,
    #     "value": {
    #         "change_type": change_type,
    #         "records_updated": records_updated,

    #     },
    # }
    key = str(key)
    value = json.dumps(value, indent=4)
    return key, value
