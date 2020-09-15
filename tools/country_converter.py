from tools import data_util

# The file that contains mappings from country names to ISO codes.
COUNTRY_DATA_FILE = "../common/countries.data"

COUNTRIES_ISO_TO_NAME = {}
COUNTRIES_NAME_TO_ISO = {}

IGNORED_COUNTRY_NAMES = [
    "Cruise Ship",
    "Diamond Princess",
    "MS Zaandam",
    "Others",
]

def initialize_country_names_and_codes():
    global COUNTRIES_ISO_TO_NAME
    global COUNTRIES_NAME_TO_ISO
    if len(COUNTRIES_ISO_TO_NAME) > 1:
        return
    COUNTRIES_ISO_TO_NAME = {}
    with open(COUNTRY_DATA_FILE) as f:
        data = f.read().strip()
        f.close()
    pairs = data.split('\n')
    for p in pairs:
        (continent, code, name, population, _) = p.split(":")
        COUNTRIES_ISO_TO_NAME[code] = name
        COUNTRIES_NAME_TO_ISO[name.lower()] = code

def get_all_countries():
    """Returns a dictionary of country ISO codes to their name."""
    return COUNTRIES_ISO_TO_NAME
    if len(COUNTRIES_ISO_TO_NAME) > 0:
        return COUNTRIES_ISO_TO_NAME


def country_code_from_name(name):
    # Are we being passed something that's already a code?
    if len(name) == 2 and name == name.upper():
        return name
    if name.lower() in COUNTRIES_NAME_TO_ISO:
        return COUNTRIES_NAME_TO_ISO[name.lower()]

def should_ignore_country(name):
    return name in IGNORED_COUNTRY_NAMES

def code_from_name(name):
    code = country_code_from_name(name)
    if code:
        return code
    return code_for_nonstandard_country_name(name)

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

# Fetch country names and codes at module initialization time to avoid doing it
# repeatedly.
initialize_country_names_and_codes()
