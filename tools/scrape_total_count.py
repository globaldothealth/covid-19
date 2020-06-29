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
    self_dir = os.path.dirname(os.path.realpath(__file__))
    out_path = os.path.join(self_dir, "latestCounts.json")
    print("Saving file as " + out_path + "...")
    scrape_total_count(out_path)
