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


def get_latest_data(outfile):
    date = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
    if fetch_one_day(date, outfile):
        return True
    # If that didn't work, try the previous day instead
    date = (datetime.now() - timedelta(days=2)).strftime('%m-%d-%Y')
    return fetch_one_day(date, outfile)

# Returns whether the operation was successful.
def fetch_one_day(date, outfile):
    url_base = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{}.csv'
    url = url_base.format(date)

    req = requests.get(url)
    if req.status_code != 200:
        print("Got status " + str(req.status_code) + " for '" + url + "'")
        return False

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
        entry = {"attributes": {"cum_conf": data[code][0], "code": code}}
        features.append(entry)

    features = sorted(features, key=lambda x: x['attributes']['cum_conf'], reverse=True)
    data = {'features': features}

    with open(outfile, 'w') as f:
        json.dump(data, f)
        f.close()

    return True


if __name__ == '__main__':
    if not get_latest_data(sys.argv[1]):
        print("Couldn't get Global JHU data, aborting.")
