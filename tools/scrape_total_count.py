import json
import os
from datetime import datetime
import pandas as pd

# Returns whether the operation was successful
def scrape_total_count(out_path):
    url = "http://opendata.ecdc.europa.eu/covid19/casedistribution/csv/"
    try:
        data = pd.read_csv(url, usecols=['cases', 'deaths'])
    except:
        print("I wasn't able to fetch the file I wanted: " + str(url))
        return False

    count = data['cases'].sum()
    deaths = data['deaths'].sum()

    date = datetime.now().strftime("%Y-%m-%d")
    results = {"caseCount": int(count), "deaths": int(deaths), "date": date}

    with open(out_path, "w") as F:
        json.dump([results], F)
    return True


if __name__ == "__main__":
    SELF_DIR = os.path.dirname(os.path.realpath(__file__))
    OUT_PATH = os.path.join(SELF_DIR, "globals.json")
    print("Saving file as " + OUT_PATH + "...")
    scrape_total_count(OUT_PATH)
