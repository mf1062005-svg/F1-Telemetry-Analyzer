"""Download OpenF1 x/y/z position samples for Bahrain 2024 Qualifying.

Requires data/drivers.csv from download_openf1_telemetry.py.
Creates data/all_drivers_location.csv.
"""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

BASE_URL = "https://api.openf1.org/v1"
SESSION_KEY = 9468
DATA_DIR = "data"
DRIVERS_FILE = os.path.join(DATA_DIR, "drivers.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "all_drivers_location.csv")


def get_data(endpoint, params, timeout=90):
    url = f"{BASE_URL}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "F1TelemetryAnalyzer/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenF1 HTTP {exc.code} sur {endpoint}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Erreur reseau OpenF1: {exc}") from exc


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DRIVERS_FILE):
        raise FileNotFoundError(f"Fichier introuvable: {DRIVERS_FILE}. Execute d'abord le telechargement OpenF1.")

    drivers = pd.read_csv(DRIVERS_FILE)
    required = {"driver_number", "name_acronym", "full_name", "team_name"}
    missing = required - set(drivers.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans drivers.csv: {sorted(missing)}")

    all_positions = []
    print(f"Telechargement des positions OpenF1 - session {SESSION_KEY}")
    for index, driver in drivers.iterrows():
        number = int(driver["driver_number"])
        code = str(driver["name_acronym"])
        print(f"[{index + 1}/{len(drivers)}] {code}...", end=" ", flush=True)
        try:
            rows = get_data("location", {"session_key": SESSION_KEY, "driver_number": number})
        except RuntimeError as exc:
            print(f"ERREUR: {exc}")
            time.sleep(.5)
            continue
        if not rows:
            print("aucune position")
            time.sleep(.5)
            continue
        frame = pd.DataFrame(rows)
        frame["driver_code"] = code
        frame["driver_name"] = str(driver["full_name"])
        frame["team_name"] = str(driver["team_name"])
        all_positions.append(frame)
        print(f"{len(frame)} points")
        time.sleep(.5)

    if not all_positions:
        raise RuntimeError("Aucune position recue. Verifie la session et la connexion.")
    result = pd.concat(all_positions, ignore_index=True)
    result["date"] = pd.to_datetime(result["date"], utc=True, errors="coerce")
    result = result.dropna(subset=["date", "x", "y"]).sort_values(["driver_number", "date"])
    result.to_csv(OUTPUT_FILE, index=False)
    print("\nTELECHARGEMENT TERMINE")
    print(f"Pilotes avec positions: {result['driver_number'].nunique()}")
    print(f"Nombre total de points: {len(result)}")
    print(f"Fichier cree: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
