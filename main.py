import json
import requests
from urllib.parse import urlparse
import time

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

def AnilistReq(ids):
    url = "https://graphql.anilist.co"
    
    payload = {
        "query": "query ($ids: [Int]) { Page(perPage: 50) { media(id_in: $ids, type: MANGA) { id externalLinks { url }}}}",
        "variables": {"ids": ids }
    }
    resp = requests.post(url, json=payload)

    return resp.json()["data"]

def main():
    allTitles = MangaPlusRequest("/title_list/allV2", {})["allTitlesViewV2"]["AllTitlesGroup"]

    result = {}
    notFound = {}

    try:
        with open("map.json", 'r') as openFile:
            result = json.load(openFile)
    except FileNotFoundError:
        result = {}

    try:
        with open("notfound.json", "r") as openFile:
            notFound = json.load(openFile)
    except FileNotFoundError:
        notFound = {}

    try:
        for title in allTitles:
            mpTitleId = title["titles"][0]["titleId"]
            if str(mpTitleId) in result:
                #print(f"SKIP: {mpTitleId}")
                for t in title["titles"]:
                    if str(t["titleId"]) in result:
                        continue
                    result[t["titleId"]] = result[str(mpTitleId)]
                    #print(f"INFO: {mpTitleId}: fixed missing other lang keys")
                if str(mpTitleId) in notFound:
                    del notFound[str(mpTitleId)]
                    #print(f"INFO: {mpTitleId}: removed from notfound")
                continue

            if str(mpTitleId) in notFound:
                print(f"WARN: {mpTitleId} was not found last time, skipping")
                continue

            mdr = MangaDexRequest("/manga", {"title":title["theTitle"], "limit": 25})
            alIds = {}

            found = False
            for manga in mdr:
                links = manga["attributes"].get("links")
                if links == None:
                    continue

                tl = []

                if "engtl" in links:
                    tl.append(urlparse(links["engtl"]))
                if "raw" in links:
                    tl.append(urlparse(links["raw"]))

                for link in tl:
                    if (link.hostname == "mangaplus.shueisha.co.jp") and int(link.path.split("/")[-1]) == int(mpTitleId):
                        found=True
                        print(f"FOUND: {mpTitleId} -> {manga["id"]}")
                        for t in title["titles"]:
                            result[t["titleId"]] = manga["id"]
                        break

                if found:
                    break

                al = links.get("al")
                if al == None:
                    continue
                alIds[al] = manga["id"]

            alr = AnilistReq(list(alIds.keys()))["Page"]["media"]
            for manga in alr:
                mdexId = alIds[str(manga["id"])]
                al = manga["externalLinks"]
                for lnk in al:
                    url = urlparse(lnk["url"])
                    if (url.hostname == "mangaplus.shueisha.co.jp" and int(url.path.split("/")[-1]) == int(mpTitleId)):
                        found=True
                        print(f"FOUND: {mpTitleId} -> {mdexId}")
                        for t in title["titles"]:
                            result[t["titleId"]] = mdexId
                        break
                if found:
                    break

            if found == False:
                notFound[mpTitleId] = title["theTitle"]
                print(f"WARN: {title["theTitle"]} not found")

            time.sleep(2)


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
