"""Befehl 14: Screenshot des Bildschirms aufnehmen und im Ordner screenshots/ des Projekts speichern."""
import mss
import os
from pathlib import Path
def screenshot():
    """Befehl 14: Nimmt einen Screenshot auf (Bibliothek mss).
    Der Dateiname wird nummeriert: Anzahl der bereits im Ordner screenshots/ vorhandenen Dateien + 1.
    Rückgabe: Satz mit der Nummer des Screenshots.
    """
    # folder path
    dir_path = Path(__file__).resolve().parent.parent.parent / "screenshots"
    count = 0
    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_path, path)):
            count += 1
    with mss.mss() as sct:
        sct.shot(output=str(dir_path / f"screenshot{count+1}.png"))
    return "Screenshot aufgenommen mit Nummer " + str(count+1)

if __name__ == "__main__":
    print(screenshot())
