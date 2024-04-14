import json
import requests
from urllib.parse import urlparse
import os.path
import time
import logging

mangaPlusApi = "https://jumpg-webapi.tokyo-cdn.com/api"
mangadexApi = "https://api.mangadex.org"


def MangaPlusRequest(endpoint, params):
    url = f"{mangaPlusApi}{endpoint}"
    params["format"] = "json"

    response = requests.get(url, params=params)

    return response.json()["success"]

def MangaDexRequest(endpoint, params):
    url = f"{mangadexApi}{endpoint}"

    respomse = requests.get(url, params=params)

    return respomse.json()["data"]

def main():
    logging.basicConfig(level=logging.DEBUG)

    allTitles = MangaPlusRequest("/title_list/allV2", {})["allTitlesViewV2"]["AllTitlesGroup"]

    notFound = {}
    flagged = {}
    result = {}

    with open("map.json", 'r') as openFile:
        result = json.load(openFile)

    with open("notfound.json", "r") as openFile:
        notFound = json.load(openFile)

    with open("flagged.json", "r") as openFile:
        flagged = json.load(openFile)

    try:
        for title in allTitles:
            mpTitleId = str(title["titles"][0]["titleId"])
            mdId = result.get(mpTitleId)
            if mdId == None:
                continue

            mdres = MangaDexRequest(f"/manga/{mdId}", {})
            mdTitles = [mdres["attributes"]["title"]["en"]] + [alt.get("en") for alt in mdres["attributes"]["altTitles"] if alt.get("en")]

            if all(x.lower() != title["theTitle"].lower() for x in mdTitles):
                flagged[mpTitleId] = {"MangaDex": mdres["attributes"]["title"]["en"], "MangaPlus": title["theTitle"]}
                print(flagged[mpTitleId])
            
            time.sleep(3)
    except Exception as e:
        with open("flagged.json", "w") as outfile:
            json.dump(flagged, outfile, indent=4)

        raise e

    with open("flagged.json", "w") as outfile:
        json.dump(flagged, outfile, indent=4)

if __name__ == "__main__":
    main()