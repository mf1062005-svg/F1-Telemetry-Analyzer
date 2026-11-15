
import json
from urllib.request import urlopen
from urllib.parse import urlencode

BASE_URL = "https://api.openf1.org/v1"


def get_data(endpoint, params):

    url = f"{BASE_URL}/{endpoint}?{urlencode(params)}"

    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


print("Connexion a OpenF1...")

try:

    # Rechercher les qualifications de Bahrein 2024
    sessions = get_data(
        "sessions",
        {
            "year": 2024,
            "country_name": "Bahrain",
            "session_name": "Qualifying"
        }
    )

    if not sessions:
        print("Aucune seance trouvee.")
        raise SystemExit

    session = sessions[0]
    session_key = session["session_key"]

    print("\nSEANCE TROUVEE")
    print("Grand Prix :", session["circuit_short_name"])
    print("Session :", session["session_name"])
    print("Session Key :", session_key)

    # Recuperer tous les pilotes
    drivers = get_data(
        "drivers",
        {"session_key": session_key}
    )

    print("\nNOMBRE DE PILOTES :", len(drivers))

    for driver in drivers:
        print(
            driver["name_acronym"],
            "-",
            driver["full_name"],
            "-",
            driver["team_name"]
        )

    print("\nTEST OPENF1 REUSSI !")

except Exception as error:
    print("\nERREUR :", error)
