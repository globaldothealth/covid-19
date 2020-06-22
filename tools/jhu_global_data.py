#!/usr/bin/env python3

from datetime import datetime, timedelta
import csv
import sys
import json

import requests

from tools import data_util

IGNORED_COUNTRY_NAMES = [
    "Diamond Princess",
    "MS Zaandam",
]

def code_for_nonstandard_country_name(name):
    if "Brunei" in name:
        return "BN"
    if "Burma" in name:
        return "MM"
    if "Congo" in name:
        if "Brazzaville" in name:
            return "CG"
        if "Kinshasa" in name:
            return "CD"
    if "Czechia" in name:
        return "CZ"
    if "Laos" in name:
        return "LA"
    if "Syria" in name:
        return "SY"
    if "Taiwan" in name:
        return "TW"
    if "Korea" in name and "South" in name:
        return "KR"
    if "United States" in name and "America" in name:
        return "US"
    if "West Bank" in name and "Gaza" in name:
        return "PS"
    return None


def get_aggregate_data(outfile):
    max_days = 1
    one_successful_fetch = False
    data = {}

    # Keep fetching data while there's more. Sometimes, depending on the time
    # of day, the data for the previous day isn't available yet. We don't give
    # up until we've had at least one successful fetch.
    days_ago = 1
    now = datetime.now()
    while days_ago <= max_days + 1:
        date = now - timedelta(days=days_ago)
        current_data = fetch_one_day(date.strftime('%m-%d-%Y'))
        if not len(current_data):
            if one_successful_fetch:
                # This is the end, my only friend
                break

        one_successful_fetch = True
        data[date.strftime("%Y-%m-%d")] = current_data
        days_ago += 1

    with open(outfile, 'w') as f:
        json.dump(data, f)
        f.close()
    return True

# Returns whether the operation was successful.
def fetch_one_day(date):
    url_base = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{}.csv'
    url = url_base.format(date)
    print(url + "...")

    req = requests.get(url)
    if req.status_code != 200:
        print("Got status " + str(req.status_code) + " for '" + url + "'")
        return []

    reader = csv.DictReader(req.text.split("\n"), delimiter=',', quotechar='"')
    features = []

    # A dictionary with country codes as keys, and values are arrays of
    # [confirmed, deaths, recovered, active]
    data = {}
    for row in reader:
        country_name = row['Country_Region'].replace('"', '')
        if country_name in IGNORED_COUNTRY_NAMES:
            continue
        code = data_util.country_code_from_name(country_name)
        if not code:
            code = code_for_nonstandard_country_name(country_name)
        if not code:
            print("I couldn't find country '" + country_name + "', please fix me.")
            sys.exit(1)
        if not code in data:
            data[code] = [0, 0, 0, 0]
        data[code][0] += int(row["Confirmed"].replace(",", ""))
        data[code][1] += int(row["Deaths"].replace(",", ""))
        data[code][2] += int(row["Recovered"].replace(",", ""))
        data[code][3] += int(row["Active"].replace(",", ""))
    for code in data:
        entry = {"cum_conf": data[code][0], "code": code}
        features.append(entry)

    features = sorted(features, key=lambda x: x['cum_conf'], reverse=True)

    return features


if __name__ == '__main__':
    if not get_aggregate_data(sys.argv[1]):
        print("Couldn't get Global JHU data, aborting.")
