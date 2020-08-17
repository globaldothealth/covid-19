import json

LAT_LNG_DECIMAL_PLACES = 5
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

def get_geo_id(case):
    if "location" not in case or "geometry" not in case["location"]:
        return None
    lat = case["location"]["geometry"]["latitude"]
    lng = case["location"]["geometry"]["longitude"]
    return str(round(lat, LAT_LNG_DECIMAL_PLACES)) + "|" + \
           str(round(lng, LAT_LNG_DECIMAL_PLACES))

def load_case_data(file_path):
    lines = []
    with open(file_path) as f:
        # The data isn't actually valid JSON, but processing each line
        # individually is easier on the RAM
        lines = f.readlines()[:100]
        f.close()
    cases = []
    for l in lines:
        cases.append(json.loads(l.strip()))
    return cases

def extract_location_info(cases, out_path):
    geo_id_to_location_info = {}
    for c in cases:
        geo_id = get_geo_id(c)
        if geo_id in geo_id_to_location_info:
            continue
        loc = c["location"]
        info = []
        for k in LOCATION_INFO_KEYS:
            if k in loc:
                info.append(loc[k])
            geo_id_to_location_info[geo_id] = "|".join(info)
    print(geo_id_to_location_info)

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
