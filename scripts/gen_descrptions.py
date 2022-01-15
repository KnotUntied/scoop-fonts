import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from github import Github

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

except_msg = """ACCESS_TOKEN is required \
(just public repo scope), \
it is read from an .env file or environment vars.\
"""

if ACCESS_TOKEN in ["", None]:
    raise Exception(except_msg)

desc_cache = {}
version_pattern = r"\n\s*\"version\": \".*\",\n"


def iterate_bucket(bucket_loc="../bucket", g=None):
    if g is None:
        g = Github(ACCESS_TOKEN)

    bucket_loc = Path(bucket_loc)

    for file in bucket_loc.iterdir():
        with open(file, "r") as f:
            try:
                j = json.load(f)
            except json.decoder.JSONDecodeError:
                print("Invalid JSON", file.name, "skipping...")
                continue
            if "description" in j:
                print(file.name, "already has a description")
                continue
            url = j["homepage"]
            desc = None
            if url.startswith("https://github.com"):
                repo = "/".join(url.split("/")[3:5])
                if repo in desc_cache:
                    desc = desc_cache[repo].strip()
                else:
                    desc = get_desc(repo, g=g)
                    if desc is not None:
                        desc_cache[repo] = desc.strip()
                    else:
                        print("No description", file.name)
            else:
                try:
                    if url in desc_cache:
                        desc = desc_cache[url].strip()
                    else:
                        r = requests.get(url)
                        soup = BeautifulSoup(r.text, features="lxml")
                        desc = soup.title.string
                        desc_cache[url] = desc.strip()
                except requests.exceptions.SSLError:
                    if file.name == "courierprime.json":
                        desc = "It's Courier, just better"
                    else:
                        desc = "It's Courier, just better - " + ".".join(file.name.split(".")[:-1]).title()
        desc = desc.strip()
        if desc.lower() == "google fonts":
            desc = desc + " - " + ".".join(file.name.split(".")[:-1]).title()

        with open(file, "w") as f:
            datastr = json.dumps(j, indent=4)
            x = {}
            x["description"] = desc
            descstr = json.dumps(x)
            m = re.search(version_pattern, datastr)
            parts = re.split(version_pattern, datastr)
            assert len(parts) == 2
            data = (
                parts[0] + m.group(0) + " " * 4 + descstr[1:][:-1] + "," + "\n" + parts[1]
            )
            f.write(data)
            f.write("\n")


def get_desc(repo, g=None):
    if g is None:
        g = Github(ACCESS_TOKEN)

    repo = g.get_repo(repo)
    return repo.description


if __name__ == "__main__":
    g = Github(ACCESS_TOKEN)
    iterate_bucket()
