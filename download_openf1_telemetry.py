import time
from urllib.error import HTTPError
import json
import os
from urllib.request import urlopen, Request
from urllib.parse import urlencode

import pandas as pd

# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = "https://api.openf1.org/v1"

YEAR = 2024
GRAND_PRIX = "Bahrain"
SESSION_NAME = "Qualifying"

os.makedirs("data/telemetry", exist_ok=True)
os.makedirs("data", exist_ok=True)


# ==========================================
# FONCTION POUR INTERROGER OPENF1
# ==========================================

def get_data(endpoint, params):

    url = f"{BASE_URL}/{endpoint}?{urlencode(params)}"

    request = Request(
        url,
        headers={"User-Agent": "F1TelemetryAnalyzer/1.0"}
    )

    try:
        with urlopen(request, timeout=90) as response:
            return json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Erreur OpenF1 {error.code} sur {endpoint}: {details}"
        )


# ==========================================
# 1. RECUPERER LA SESSION
# ==========================================

print("\nConnexion a OpenF1...")

sessions = get_data(
    "sessions",
    {
        "year": YEAR,
        "country_name": GRAND_PRIX,
        "session_name": SESSION_NAME
    }
)

if not sessions:
    raise RuntimeError("Session introuvable.")

session = sessions[0]
session_key = session["session_key"]

print("\nSESSION :", session["session_name"])
print("GRAND PRIX :", session["circuit_short_name"])
print("SESSION KEY :", session_key)


# ==========================================
# 2. RECUPERER TOUS LES PILOTES
# ==========================================

print("\nRecuperation des pilotes...")

drivers = get_data(
    "drivers",
    {"session_key": session_key}
)

if not drivers:
    raise RuntimeError("Aucun pilote trouve.")

drivers_df = pd.DataFrame(drivers)
drivers_df.to_csv(
    "data/drivers.csv",
    index=False
)

# Correspondance numero -> nom et equipe
driver_codes = {
    int(d["driver_number"]): d["name_acronym"]
    for d in drivers
}

driver_names = {
    int(d["driver_number"]): d["full_name"]
    for d in drivers
}

driver_teams = {
    int(d["driver_number"]): d["team_name"]
    for d in drivers
}

print("Nombre de pilotes :", len(drivers))



# ==========================================
# 3. RECUPERER LA TELEMETRIE PILOTE PAR PILOTE
# ==========================================

print("\nTelechargement de la telemetrie...")

all_telemetry = []

for index, driver in enumerate(drivers, start=1):

    number = int(driver["driver_number"])
    code = driver["name_acronym"]

    print(
        f"\n[{index}/{len(drivers)}] "
        f"Telechargement de {code}..."
    )

    # Demander uniquement les donnees de ce pilote
    car_data = get_data(
        "car_data",
        {
            "session_key": session_key,
            "driver_number": number
        }
    )

    if not car_data:
        print(f"{code} : aucune telemetrie disponible")
        continue

    driver_data = pd.DataFrame(car_data)

    # Ajouter les informations du pilote
    driver_data["driver_code"] = code
    driver_data["driver_name"] = driver["full_name"]
    driver_data["team_name"] = driver["team_name"]

    # Sauvegarder le CSV individuel
    driver_data.to_csv(
        f"data/telemetry/{code}_telemetry.csv",
        index=False
    )

    all_telemetry.append(driver_data)

    print(
        f"{code} : {len(driver_data)} "
        "echantillons sauvegardes"
    )

    # Respecter la limite de requetes gratuites
    time.sleep(0.5)


# Regrouper toutes les donnees
if all_telemetry:

    telemetry_df = pd.concat(
        all_telemetry,
        ignore_index=True
    )

    telemetry_df.to_csv(
        "data/all_drivers_telemetry.csv",
        index=False
    )

    print("\nTELEMETRIE TELECHARGEE !")

    print(
        "Nombre de pilotes :",
        telemetry_df["driver_number"].nunique()
    )

    print(
        "Nombre total d'echantillons :",
        len(telemetry_df)
    )

else:

    print("Aucune telemetrie recuperable.")
    raise RuntimeError("Aucune donnee de voiture disponible.")

# ==========================================
# 4. RECUPERER LES TEMPS AU TOUR
# ==========================================

print("\nRecuperation des temps au tour...")

laps_data = get_data(
    "laps",
    {"session_key": session_key}
)

laps_df = pd.DataFrame(laps_data)

if not laps_df.empty:

    laps_df["driver_code"] = laps_df[
        "driver_number"
    ].map(driver_codes)

    laps_df.to_csv(
        "data/all_drivers_laps.csv",
        index=False
    )

    valid_laps = laps_df.dropna(
        subset=["lap_duration"]
    ).copy()

    if "is_pit_out_lap" in valid_laps.columns:
        valid_laps = valid_laps[
            ~valid_laps["is_pit_out_lap"].fillna(False)
        ]

    best_laps = (
        valid_laps
        .sort_values("lap_duration")
        .groupby("driver_number", as_index=False)
        .first()
        .sort_values("lap_duration")
    )

    best_laps.to_csv(
        "data/all_drivers_best_laps.csv",
        index=False
    )

    print("\nCLASSEMENT DES MEILLEURS TOURS :")

    print(
        best_laps[
            [
                "driver_code",
                "lap_number",
                "lap_duration"
            ]
        ].to_string(index=False)
    )

else:
    print("Aucune donnee de tour disponible.")


# ==========================================
# 5. FIN
# ==========================================

print("\n================================")
print("TELECHARGEMENT TERMINE !")
print("================================")

print(
    "Total echantillons :",
    len(telemetry_df)
)

print(
    "Pilotes avec telemetrie :",
    telemetry_df["driver_number"].nunique()
)

print("\nVerifie le dossier data/telemetry/")
