import json
import requests
from urllib.parse import urlparse
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

def AnilistReq(id):
    url = "https://graphql.anilist.co"
    payload = {
        "query": "query($_id: Int) { Media(id: $_id) { externalLinks { url } } }",
        "variables": {"_id": id }
    }
    resp = requests.post(url, json=payload)

    return resp.json()["data"]

def main():
    logging.basicConfig(level=logging.DEBUG)

    allTitles = MangaPlusRequest("/title_list/allV2", {})["allTitlesViewV2"]["AllTitlesGroup"]

    result = {}
    notFound = {}

    with open("map.json", 'r') as openFile:
        result = json.load(openFile)

    with open("notfound.json", "r") as openFile:
        notFound = json.load(openFile)

    try:
        for title in allTitles:
            mpTitleId = title["titles"][0]["titleId"]
            if str(mpTitleId) in result:
                print(f"{mpTitleId} already exists in file, bailing")
                for t in title["titles"]:
                    if str(t["titleId"]) in result:
                        continue
                    result[t["titleId"]] = result[str(mpTitleId)]
                    print("\talso fixed missing other lang keys ;)")
                if str(mpTitleId) in notFound:
                    del notFound[str(mpTitleId)]
                    print("\talso removed it from notfound :D")
                continue

            if str(mpTitleId) in notFound:
                print(f"{mpTitleId} was not found last time, bailing")
                continue

            mdr = MangaDexRequest("/manga", {"title":title["theTitle"], "limit":"1"})
            found = False
            for manga in mdr:
                links = manga["attributes"].get("links")
                if links == None:
                    continue

                link1 = links.get("engtl", "https://127.0.0.1/not-real")
                url1 = urlparse(link1)

                link2 = links.get("raw", "https://127.0.0.1/not-real")
                url2 = urlparse(link2)

                if (url1.hostname == "mangaplus.shueisha.co.jp" and int(link1.split("/")[-1]) == int(mpTitleId)) or (url2.hostname == "mangaplus.shueisha.co.jp" and int(link2.split("/")[-1]) == int(mpTitleId)):
                    found=True
                    print(mpTitleId, "->", manga["id"])
                    for t in title["titles"]:
                        result[t["titleId"]] = manga["id"]
                    break
                else:
                    al = links.get("al")
                    if al == None:
                        continue
                    alr = AnilistReq(al)["Media"]["externalLinks"]
                    for lnk in alr:
                        url3 = urlparse(lnk["url"])
                        if (url3.hostname == "mangaplus.shueisha.co.jp" and int(lnk["url"].split("/")[-1]) == int(mpTitleId)):
                            found=True
                            print(mpTitleId, "->", manga["id"])
                            for t in title["titles"]:
                                result[t["titleId"]] = manga["id"]
                            break

                    if found:
                        break

                time.sleep(2)

            if found == False:
                notFound[mpTitleId] = title["theTitle"]
                print(f"Warning: {title["theTitle"]} not found, bailing")


    except Exception as e:
        with open("map.json", "w") as outfile:
            json.dump(result, outfile, indent=4)

        with open("notfound.json", "w") as outfile:
            json.dump(notFound, outfile, indent=4)

        raise e

    with open("map.json", "w") as outfile:
        json.dump(result, outfile, indent=4)

    with open("notfound.json", "w") as outfile:
        json.dump(notFound, outfile, indent=4)

if (__name__ == "__main__"):
    main()
