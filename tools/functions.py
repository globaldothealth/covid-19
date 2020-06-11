LAT_LNG_DECIMAL_PLACES = 4

def round_lat_long(lat_or_lng):
    return str(round(float(lat_or_lng), LAT_LNG_DECIMAL_PLACES))
