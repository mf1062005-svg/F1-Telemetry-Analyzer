
from pathlib import Path
from PIL import Image

# Dossier contenant les images
ASSETS = Path(__file__).resolve().parent / "assets"

print("\n===== VERIFICATION DES IMAGES =====\n")

valid = 0
invalid = 0

for path in ASSETS.rglob("*"):

    if not path.is_file():
        continue

    try:
        # Verifier que Pillow peut lire le fichier
        with Image.open(path) as img:
            img.verify()

        # Relire pour obtenir le format et les dimensions
        with Image.open(path) as img:
            print(
                f"OK       | {path.name} | "
                f"{img.format} | {img.size}"
            )

        valid += 1

    except Exception as error:

        print(
            f"INVALIDE | {path.name} | "
            f"{type(error).__name__}: {error}"
        )

        invalid += 1

print("\n===== RESULTAT =====")
print("Images valides :", valid)
print("Images invalides :", invalid)
