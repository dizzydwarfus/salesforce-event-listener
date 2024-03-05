import json
import pandas as pd
import logging
import requests
import datetime

from requests.auth import HTTPBasicAuth

import auth


def get_cookies(username, password, companydb="BASF_DE_PROD"):
    """
    function to perform digest-auth on sap db and return the pre-formatted cookies to put into a request

    :param username: username for sap db
    :param password: password for sap db
    :param companydb: name for the sap db
    :return: formatted cookie to put in request
    """
    cookies = {}

    data = json.dumps(
        {"UserName": username, "Password": password, "CompanyDB": companydb}
    )
    session = requests.Session()

    respone = session.post(
        "https://su-2105-123.emea.businessone.cloud.sap/b1s/v1/Login", data=data
    )

    # headers = respone.cookies
    sessionid = json.loads(respone.text)["SessionId"]

    # test 1: Welche Header kommen zurück?
    # for header in headers:
    #   cookies.update({header.name: header.value})

    cookies = session.cookies.get_dict()

    print(
        "ROUTEID={routeid}; Path=/;B1SESSION={sessionid}; Path=/b1s/v1; HttpOnly;".format(
            routeid=cookies.get("ROUTEID"), sessionid=cookies.get("B1SESSION")
        )
    )
    return cookies


logging.basicConfig(filename="C:/TableauExtract/BASF/exeption.log", level=logging.DEBUG)

pathSrc = "C:/TableauExtract/BASF/"
path = "//fp1.basf-3dps.com/share/27_Finance Data/274_SAP/"

date_today = str(datetime.date.today())


service = "https://su-2105-123.emea.businessone.cloud.sap/b1s/v1/sml.svc/"

username = auth.username
password = auth.password
headers = {"Prefer": "odata.maxpagesize=0"}
# params = {'$top': '1000'}

my_auth = HTTPBasicAuth(username, password)


f = open(pathSrc + "01_SAP_Queries.txt", "r")

for q in f:
    query = q.rstrip()
    try:
        url = service + query

        cookies = get_cookies(username=auth.username, password=auth.password)
        r = requests.get(url=url, headers=headers, cookies=cookies)
        # API Results
        data = r.text
        my_json = json.loads(data)
        value = my_json["value"]
        # rows list initialization
        rows = []
        # appending rows
        for row in value:
            rows.append(row)
        # get nextLink if JSON does contain one
        if "@odata.nextLink" in my_json:
            next_link = my_json["@odata.nextLink"]
            # repeat as long as the response contains a nextLink
            while next_link:
                # same logic as before but with updated url from JSON response
                url = service + next_link
                r = requests.get(url=url, headers=headers, cookies=cookies)
                data = r.text
                my_json = json.loads(data)
                value = my_json["value"]
                # append next values to the same list as the initial values
                for row in value:
                    rows.append(row)
                # get the next link if the new response still contains one
                if "@odata.nextLink" in my_json:
                    next_link = my_json["@odata.nextLink"]
                else:
                    break

        # using data frame
        df = pd.DataFrame(rows)

        # Write to .CSV
        df.to_csv(path + query + ".csv", index=False, header=True, decimal=",", sep=";")
        # Write log
        log = "success" + ";" + query + ";" + str(datetime.datetime.today())
        log_df = pd.DataFrame([x.split(";") for x in log.split("\n")])
        log_df.to_csv(
            pathSrc + date_today + "_log.csv",
            index=False,
            header=False,
            sep=";",
            mode="a",
        )
        # print('Export finished: ' + query)
    except Exception as e:
        # Write log
        log = "error " + ";" + query + ";" + str(datetime.datetime.today()) + "\n" + e
        log_df = pd.DataFrame([x.split(";") for x in log.split("\n")])
        log_df.to_csv(
            pathSrc + date_today + "_log.csv",
            index=False,
            header=False,
            sep=";",
            mode="a",
        )
        # print('Could not export: ' + query)
