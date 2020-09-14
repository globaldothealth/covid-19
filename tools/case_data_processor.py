import json
import os

from tools import country_converter
from tools import data_util

LAT_LNG_DECIMAL_PLACES = 4
LOCATION_INFO_KEYS = ["administrativeAreaLevel" + str(n) for n in [1, 2, 3]]

def get_confirm_date(case):
    # TODO: We might want to average the start and end of a date range.
    if "events" not in case:
        return None
    events = case["events"]
    for e in events:
        if e["name"] == "confirmed":
            return e["dateRange"]["start"]["$date"][:len("YYY-MM-DD") + 1]
    return None

def normalize_geo_id(in_geo_id):
    (lat, lng) = [float(l) for l in in_geo_id.split("|")]
    return normalize_latlng(lat) + "|" + normalize_latlng(lng)

def normalize_latlng(latlng):
    latlng = str(latlng)
    if "." not in latlng:
        latlng += ".0"
    (int_part, dec_part) = str(latlng).split(".")
    if len(dec_part) == LAT_LNG_DECIMAL_PLACES:
        return str(latlng)
    if len(dec_part) > LAT_LNG_DECIMAL_PLACES:
        return int_part + "." + dec_part[:LAT_LNG_DECIMAL_PLACES]
    dec_part = dec_part + "0" * (LAT_LNG_DECIMAL_PLACES - len(dec_part))
    return int_part + "." + dec_part

def get_geo_id(case):
    if "location" not in case or "geometry" not in case["location"]:
        return None
    lat = case["location"]["geometry"]["latitude"]
    lng = case["location"]["geometry"]["longitude"]
    return normalize_latlng(lat) + "|" + normalize_latlng(lng)

def load_case_data(file_path):
    lines = []
    with open(file_path) as f:
        cases = json.loads(f.read())
        f.close()
    return cases

def add_or_replace_if_more_precise(data, geo_id, loc_info):
    if geo_id not in data:
        data[geo_id] = loc_info
        return
    # If the data already contains this geo ID, we assume a longer info string
    # means more precision
    existing = data[geo_id]
    if len(loc_info) > len(existing):
        data[geo_id] = loc_info

def extract_location_info(cases, out_path):
    geo_id_to_location_info = {}
    # Start by reading the existing data
    with open(out_path) as f:
        lines = f.readlines()
        f.close()
    print("Reading " + str(len(lines)) + " of existing location data...")
    for l in lines:
        (geo_id, loc_info) = l.strip().split(":", 1)
        geo_id = normalize_geo_id(geo_id)
        geo_id_to_location_info[geo_id] = loc_info
    print("Processing " + str(len(cases)) + " cases...")
    cases_without_country = 0
    example_countryless_case = None
    for c in cases:
        geo_id = get_geo_id(c)
        loc = c["location"]
        info = []
        if "country" not in loc:
            if "administrativeAreaLevel1" in loc and loc["administrativeAreaLevel1"].lower() == "taiwan":
                loc["country"] = "Taiwan"
            else:
                cases_without_country += 1
                if not example_countryless_case:
                    example_countryless_case = c
                continue
        country_code = country_converter.code_from_name(loc["country"])
        if not country_code:
            continue
        for k in LOCATION_INFO_KEYS:
            if k in loc:
                info.append(loc[k])
        info.append(country_code)
        add_or_replace_if_more_precise(
            geo_id_to_location_info, geo_id, "|".join(info))

    output = []
    if cases_without_country > 0:
        print("Warning, " + str(cases_without_country) + " "
              "cases didn't have a country. Here is an example:")
        print(example_countryless_case)
    for geo_id in geo_id_to_location_info:
        output.append(geo_id + ":" + geo_id_to_location_info[geo_id])

    with open(out_path, "w") as f:
        f.write("\n".join(output))
        f.close()

def prune_cases(cases):
    # Let's only keep the data we need. Discard textual location info, it can
    # be retrieved from the geo ID.
    pruned_cases = []
    for c in cases:
        if "location" not in c:
            continue
        confirm_date = get_confirm_date(c)
        if not confirm_date:
            continue
        pruned = {
            "geo_id": get_geo_id(c),
            "date": confirm_date
        }
        pruned_cases.append(pruned)
    return pruned_cases

def format_single_feature(geo_id, total, new):
    if new > 0:
        return {"properties": {"geoid": geo_id, "total": total, "new": new}}
    return {"properties": {"geoid": geo_id, "total": total}}

def write_daily_slice_from_accumulator(out_dir, date, acc):
    out_file = os.path.join(out_dir, date + ".json")
    print(out_file)
    out_object = {"date": date, "features": []}
    # Iterate over sorted keys to minimize file update diffs
    for geo_id in sorted(acc.keys()):
        cases = acc[geo_id]
        out_object["features"].append(format_single_feature(geo_id, cases[0], cases[1]))
    # print(out_object)
    with open(out_file, "w") as f:
        f.write(json.dumps(out_object))
        f.close()

def fold_new_cases_to_total(acc):
    for geo_id in acc:
        acc[geo_id][0] += acc[geo_id][1]
        acc[geo_id][1] = 0

def output_daily_slices(cases, out_dir):
    # Dict by date, then by geo ID, then an array of [total, new].
    new_cases_by_date_and_geo_id = {}
    cases_by_date = {}
    for c in cases:
        date = c["date"]
        if date not in cases_by_date:
            cases_by_date[date] = []
        cases_by_date[date].append(c)

    for date in sorted(cases_by_date.keys()):
        if date not in new_cases_by_date_and_geo_id:
            new_cases_by_date_and_geo_id[date] = {}
        cur_cases = cases_by_date[date]
        #print(date)
        for c in cur_cases:
            geo_id = c["geo_id"]
            if not geo_id:
                continue
            if geo_id not in new_cases_by_date_and_geo_id[date]:
                new_cases_by_date_and_geo_id[date][geo_id] = 0
            new_cases_by_date_and_geo_id[date][geo_id] += 1

    # We now have all the new cases. Now we need to accumulate and output
    # daily slices.
    # Dict by geo_id where keys are [total, new]
    acc = {}
    for date in sorted(cases_by_date.keys()):
        for geo_id in new_cases_by_date_and_geo_id[date]:
            if geo_id not in acc:
                acc[geo_id] = [0, 0]
            acc[geo_id][1] += new_cases_by_date_and_geo_id[date][geo_id]
        write_daily_slice_from_accumulator(out_dir, date, acc)
        fold_new_cases_to_total(acc)

def output_country_slices(cases, out_dir):
    pass
