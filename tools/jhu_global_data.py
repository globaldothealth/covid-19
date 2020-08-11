#!/usr/bin/env python3

from datetime import datetime, timedelta
import csv
import sys
import json

import requests

from tools import data_util

IGNORED_COUNTRY_NAMES = [
    "Cruise Ship",
    "Diamond Princess",
    "MS Zaandam",
    "Others",
]

def code_for_nonstandard_country_name(name):
    if "Brunei" in name:
        return "BN"
    if "Burma" in name:
        return "MM"
    if "Congo" in name:
        if "Brazzaville" in name:
            return "CG"
        if "Kinshasa" in name or "Democratic" in name:
            return "CD"
        return "CG"
    if "Czechia" in name:
        return "CZ"
    if "Laos" in name:
        return "LA"
    if "Bahamas" in name:
        return "BS"
    if name.startswith("Ca") and "Verde" in name:
        return "CV"
    if "China" in name:
        return "CN"
    if name.startswith("Cura") and name.endswith("ao"):
        return "CW"
    if "Gambia" in name:
        return "GM"
    if "Hong" in name:
        return "HK"
    if "Iran" in name:
        return "IR"
    if "Ireland" in name:
        return "IE"
    if "Ivo" in name:
        return "CI"
    if "Macau" in name or "Macao" in name:
        return "MO"
    if "Martin" in name and ("Saint" in name or "St" in name):
        return "MF"
    if "Moldova" in name:
        return "MD"
    if "Russia" in name:
        return "RU"
    if name.startswith("Saint Barth"):
        return "BL"
    if "Syria" in name:
        return "SY"
    if "Taiwan" in name:
        return "TW"
    if "Korea" in name:
        if "North" in name or "Democratic" in name:
            return "KP"
        return "FR"
    if "United States" in name and "America" in name:
        return "US"
    if "Taipei" in name:
        # Assume they meant Taiwan.
        return "TW"
    if "Timor" in name:
        return "TL"
    if "Vatican" in name:
        return "VA"
    if "Viet" in name:
        return "VN"
    if ("West Bank" in name and "Gaza" in name) or "Palestin" in name:
        return "PS"
    return None


def get_aggregate_data(outfile):
    print("Fetching aggregate data...")
    max_days = 365
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
    print(date, end="  ", flush=True)

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
        key = "Country_Region"
        if key not in row:
            key = "Country/Region"
        country_name = row[key].replace('"', '').strip()
        if country_name in IGNORED_COUNTRY_NAMES:
            continue
        code = data_util.country_code_from_name(country_name)
        if not code:
            code = code_for_nonstandard_country_name(country_name)
        if not code:
            print("Note: I couldn't find country '" + country_name + "'")
            continue
        if not code in data:
            data[code] = [0, 0, 0, 0]
        keys = ["Confirmed", "Deaths", "Recovered", "Active"]
        for i in range(len(keys)):
            key = keys[i]
            if key in row and row[key] != "":
                data[code][i] += int(row[key].replace(",", ""))
    for code in data:
        entry = {"cum_conf": data[code][0], "deaths": data[code][1], "code": code}
        features.append(entry)

    features = sorted(features, key=lambda x: x['cum_conf'], reverse=True)

    return features


if __name__ == '__main__':
    if not get_aggregate_data(sys.argv[1]):
        print("Couldn't get Global JHU data, aborting.")
