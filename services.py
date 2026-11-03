import requests
import database as db

WB_API_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date=2010:2023&format=json"

INDICATORS_MAP = {
    "GDP": "NY.GDP.MKTP.CD",
    "Population": "SP.POP.TOTL",
    "Inflation": "FP.CPI.TOTL.ZG",
}


def fetch_world_bank_data(country_code, indicator_key):
    indicator_code = INDICATORS_MAP.get(indicator_key, "NY.GDP.MKTP.CD")
    url = WB_API_URL.format(country=country_code, indicator=indicator_code)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                parsed_results = []
                for entry in data[1]:
                    if entry.get("value") is not None:
                        c_code = entry["countryiso3code"]
                        yr = int(entry["date"])
                        is_saved = db.is_indicator_saved(c_code, indicator_key, yr)

                        parsed_results.append({
                            "country_code": c_code,
                            "country_name": entry["country"]["value"],
                            "indicator_name": indicator_key,
                            "value": round(entry["value"], 2),
                            "year": yr,
                            "is_saved": is_saved,
                        })
                return parsed_results, None
            return [], "No data found for this query."
        return [], "External API returned an error."
    except requests.RequestException:
        return [], "Failed to connect to World Bank API."