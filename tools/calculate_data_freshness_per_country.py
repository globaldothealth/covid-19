#!/usr/bin/python3

import json
import os

SELF_DIR = os.path.dirname(os.path.realpath(__file__))
COUNTRIES_DIR = os.path.join(SELF_DIR, "..", "c")
COUNTRY_FILES = [f for f in os.listdir(COUNTRIES_DIR) if f.endswith(".json")]

def get_freshness(out_path):
    "Returns whether the operation was a success."
    if len(COUNTRY_FILES) == 0:
        print("I haven't found any data in " + COUNTRIES_DIR + ", aborting.")
        return False

    country_to_freshness_date = {}

    for country_file in COUNTRY_FILES:
        code = country_file.replace(".json", "")
        with open(os.path.join(COUNTRIES_DIR, country_file)) as f:
            data = json.loads(f.read())
            f.close()
        latest_date = ""
        for date in data:
            if date > latest_date:
                latest_date = date
        country_to_freshness_date[code] = latest_date

    with open(out_path, "w") as f:
        f.write(json.dumps(country_to_freshness_date, sort_keys=True))
        f.close()

    return True
