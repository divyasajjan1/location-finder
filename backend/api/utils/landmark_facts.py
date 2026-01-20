import requests

def get_landmark_facts(landmark_name):
    title = landmark_name.replace("_", " ")
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title

    resp = requests.get(url, headers={"User-Agent": "location-finder"})
    if resp.status_code != 200:
        return None

    data = resp.json()
    return data.get("extract")
