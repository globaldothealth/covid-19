from tools import data_util

LAT_LNG_DECIMAL_PLACES = 4

def round_lat_long(lat_or_lng):
    return str(round(float(lat_or_lng), LAT_LNG_DECIMAL_PLACES))


def compile_location_info(in_data, out_file,
                          keys=["country", "province", "city"], quiet=False):

    if not quiet:
        print("Exporting location info...")
    location_info = {}
    for item in in_data:
        geo_id = item['geoid']
        if geo_id not in location_info:
            name = str(item[keys[0]])
            # 2-letter ISO code for the country
            if name == "nan":
                code = ""
            else:
                code = data_util.country_code_from_name(name)
            location_info[geo_id] = [(str(item[key]) if str(item[key]) != "nan"
                                      else "") for key in
                                     [keys[2], keys[1]]] + [code]

    output = []
    for geoid in location_info:
        output.append(geoid + ":" + ",".join(location_info[geoid]))
    with open(out_file, "w") as f:
        f.write("\n".join(output))
        f.close()
