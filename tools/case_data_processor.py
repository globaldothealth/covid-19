import json

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
        # The data isn't actually valid JSON, but processing each line
        # individually is easier on the RAM
        lines = f.readlines()
        f.close()
    cases = []
    for l in lines:
        cases.append(json.loads(l.strip()))
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
    for l in lines:
        (geo_id, loc_info) = l.strip().split(":", 1)
        geo_id = normalize_geo_id(geo_id)
        geo_id_to_location_info[geo_id] = loc_info
    for c in cases:
        geo_id = get_geo_id(c)
        loc = c["location"]
        info = []
        if "country" not in loc:
            print("Warning, no country: " + str(c))
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
    print(geo_id_to_location_info)
    for geo_id in geo_id_to_location_info:
        output.append(geo_id + ":" + geo_id_to_location_info[geo_id])

    with open(out_path, "w") as f:
        f.write("\n".join(output))
        f.close()

def prune_cases(cases):
    # Let's only keep the data we need.
    pruned_cases = []
    for c in cases:
        if "location" not in c:
            continue
        confirm_date = get_confirm_date(c)
        if not confirm_date:
            continue
        pruned = {
            "location": c["location"],
            "geo_id": get_geo_id(c),
            "date": confirm_date
        }
        pruned_cases.append(pruned)
    return pruned_cases
