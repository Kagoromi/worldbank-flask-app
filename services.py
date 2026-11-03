import re
from datetime import date

import requests

import database as db

WB_API_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
START_YEAR = 2010

INDICATORS_MAP = {
    "GDP": "NY.GDP.MKTP.CD",
    "Population": "SP.POP.TOTL",
    "Inflation": "FP.CPI.TOTL.ZG",
}

COUNTRY_CODE_RE = re.compile(r"[A-Za-z]{2,3}")


def fetch_world_bank_data(country_code, indicator_key):
    """Fetch indicator values from the World Bank API.

    Returns a tuple (results, error). On success error is None.
    """
    if not COUNTRY_CODE_RE.fullmatch(country_code or ""):
        return [], "Invalid country code. Use 2-3 letters, for example UKR or US."

    indicator_code = INDICATORS_MAP.get(indicator_key, "NY.GDP.MKTP.CD")
    url = WB_API_URL.format(country=country_code, indicator=indicator_code)
    params = {
        "date": f"{START_YEAR}:{date.today().year}",
        "format": "json",
        "per_page": 100,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return [], "External API returned an error."

        data = response.json()
        if not (isinstance(data, list) and len(data) > 1 and data[1]):
            return [], "No data found for this query."

        # One database query for the whole response instead of one per row.
        saved_keys = db.get_saved_keys(indicator_key)

        parsed_results = []
        for entry in data[1]:
            if entry.get("value") is None:
                continue
            c_code = entry["countryiso3code"]
            year = int(entry["date"])
            parsed_results.append(
                {
                    "country_code": c_code,
                    "country_name": entry["country"]["value"],
                    "indicator_name": indicator_key,
                    "value": round(entry["value"], 2),
                    "year": year,
                    "is_saved": (c_code, year) in saved_keys,
                }
            )
        return parsed_results, None

    except requests.RequestException:
        return [], "Failed to connect to World Bank API."
    except (ValueError, KeyError, TypeError):
        return [], "Unexpected response from World Bank API."