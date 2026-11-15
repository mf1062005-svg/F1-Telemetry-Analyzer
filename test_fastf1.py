
import fastf1
import pandas as pd
import os

# 1. Creer les dossiers necessaires
os.makedirs("data/fastf1_cache", exist_ok=True)
os.makedirs("data/telemetry", exist_ok=True)

# 2. Activer le cache FastF1
fastf1.Cache.enable_cache("data/fastf1_cache")

# 3. Choisir la seance
year = 2024
grand_prix = "Bahrain"
session_type = "Q"  # Q = Qualifications

print("Chargement de la seance...")

session = fastf1.get_session(
    year,
    grand_prix,
    session_type
)

# 4. Charger les donnees reelles
session.load(
    telemetry=True,
    laps=True,
    weather=False,
    messages=False
)

print("Seance chargee avec succes !")

# DIAGNOSTIC : verifier les donnees chargees

print("\n========== DIAGNOSTIC ==========")

print("Nombre de pilotes :", len(session.drivers))
print("Liste des pilotes :", session.drivers)
print("Nombre total de tours :", len(session.laps))
print("Tours vides :", session.laps.empty)

print("Nombre de résultats :", len(session.results))
print("Résultats vides :", session.results.empty)

if "Driver" in session.laps.columns:
    print("Pilotes présents dans les tours :")
    print(session.laps["Driver"].dropna().unique())

print("Colonnes des résultats :")
print(session.results.columns.tolist())
print("Nombre total de tours :", len(session.laps))

print("Colonnes disponibles :")
print(session.laps.columns.tolist())

if not session.laps.empty:

    columns_to_show = [
        col for col in [
            "Driver",
            "DriverNumber",
            "LapNumber",
            "LapTime"
        ]
        if col in session.laps.columns
    ]

    print("\nApercu des 15 premiers tours :")
    print(
        session.laps[columns_to_show]
        .head(15)
        .to_string(index=False)
    )

    if "LapTime" in session.laps.columns:
        valid_laps = session.laps.dropna(subset=["LapTime"])

        print("\nNombre de tours avec temps valide :", len(valid_laps))

        print("\nExemple de tours valides :")
        print(
            valid_laps[columns_to_show]
            .head(10)
            .to_string(index=False)
        )

print("\n================================")

# 5. Extraire les donnees de tous les pilotes
all_best_laps = []

for driver_number in session.drivers:

    driver_laps = session.laps.pick_drivers(driver_number)

    # Garder uniquement les tours avec un temps valide
    driver_laps = driver_laps.dropna(subset=["LapTime"])

    if driver_laps.empty:
        continue

    fastest_lap = driver_laps.pick_fastest()
    driver_code = fastest_lap["Driver"]

    print(f"Extraction de {driver_code}...")

    try:
        # Recuperer la telemetrie du meilleur tour
        telemetry = fastest_lap.get_telemetry()
        telemetry = telemetry.add_distance()

        columns = [
            "Distance",
            "Speed",
            "Throttle",
            "Brake",
            "RPM",
            "nGear"
        ]

        telemetry[columns].to_csv(
            f"data/telemetry/{driver_code}_telemetry.csv",
            index=False
        )

        # Enregistrer le meilleur tour
        all_best_laps.append({
            "Driver": driver_code,
            "LapNumber": fastest_lap["LapNumber"],
            "LapTime": fastest_lap["LapTime"]
        })

    except Exception as error:
        print(f"Erreur pour {driver_code}: {error}")

# 6. Creer le classement
results = pd.DataFrame(all_best_laps)

if not results.empty:

    results = results.sort_values("LapTime")

    results.to_csv(
        "data/all_drivers_best_laps.csv",
        index=False
    )

    print("\nCLASSEMENT DES PILOTES")
    print(results.to_string(index=False))

    print("\nExtraction terminee !")

else:
    print("Aucun tour valide n'a ete recupere.")
