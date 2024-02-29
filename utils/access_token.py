import requests


def generate_access_token(domain: str, data: dict):
    response = requests.post(f"{domain}/services/oauth2/token", data=data)
    response.raise_for_status()
    return response.json()


def upsert_access_token(access_token: str):
    with open(".env", "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith("ACCESS_TOKEN"):
                lines[i] = f"ACCESS_TOKEN = {access_token}\n"
                break
    with open(".env", "w") as file:
        file.writelines(lines)

    return 0
